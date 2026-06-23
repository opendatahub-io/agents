import os
import shutil
import argparse
from collections.abc import Generator, AsyncGenerator
from queue import Queue

import anyio

import uvicorn

from dotenv import load_dotenv

import mlflow
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse, ResponsesAgentStreamEvent
from mlflow.genai.agent_server import AgentServer, invoke, stream

from openai import AsyncClient
from agents import Agent, Runner, StreamEvent, set_default_openai_client
from agents.mcp import MCPServerStdio


# ---------------------------------------------------------------------------
# Load .env and define runtime constants
# ---------------------------------------------------------------------------
load_dotenv()
UV_EXE = shutil.which("uv")
if UV_EXE is None:
    raise ValueError("Requires 'uv' executable for MCP server environment management.")

MCP_ARGS = ["run", "fastmcp", "run", "./nps_mcp_server.py"]
MCP_ENV = {**os.environ, "NPS_API_KEY": os.environ.get("NPS_API_KEY", "")}
MCP_PARAMS = {"command": UV_EXE, "args": MCP_ARGS, "env": MCP_ENV}
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o")


# ---------------------------------------------------------------------------
# Create an NPS Agent  (same pattern as 1_develop/2_evaluate.ipynb)
# ---------------------------------------------------------------------------
AGENT_NAME = "NPS Agent"
AGENT_INSTRUCTIONS = (
    "You are a helpful National Parks Service assistant. "
    "Use the available tools to answer questions about national parks, "
    "events, activities, campgrounds, and visitor information. "
)


# Configure OpenAI-compatible endpoint
async_client = AsyncClient(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
set_default_openai_client(client=async_client)


async def run_nps_agent(prompt) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    async with MCPServerStdio(params=MCP_PARAMS) as mcp_server:
        # Create the agent
        agent = Agent(
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model=OPENAI_MODEL_NAME,
        )

        # Run the agent
        result = await Runner.run(agent, prompt)
        return result.final_output


async def run_streaming_nps_agent(prompt) -> AsyncGenerator[StreamEvent, None]:
    """Run the NPS agent with MCP tools and stream the text response."""
    async with MCPServerStdio(params=MCP_PARAMS) as mcp_server:
        # Create the agent
        agent = Agent(
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model=OPENAI_MODEL_NAME,
        )

        # Run the agent with streaming
        streaming_result = Runner.run_streamed(agent, prompt)
        async for event in streaming_result.stream_events():
            yield event


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent — wraps run_nps_agent to provide tracing
# ---------------------------------------------------------------------------
class NPSResponsesAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        try:
            with anyio.from_thread.start_blocking_portal() as portal:
                result = portal.call(run_nps_agent, request.input)
        except Exception as e:
            result = f"Error: {e}"
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=result, id="msg_1")]
        )

    def predict_stream(self, request: ResponsesAgentRequest) -> Generator[ResponsesAgentStreamEvent, None, None]:

        QMSG_EVENT = "event"
        QMSG_ERROR = "error"
        QMSG_DONE = "done"
        stream_event_queue = Queue()

        async def _event_queue_producer():
            try:
                async for event in run_streaming_nps_agent(request.input):
                    stream_event_queue.put((QMSG_EVENT, event))
            except Exception as e:
                stream_event_queue.put((QMSG_ERROR, str(e)))
            finally:
                stream_event_queue.put((QMSG_DONE, None))

        with anyio.from_thread.start_blocking_portal() as portal:
            task_future = portal.start_task_soon(_event_queue_producer)

            accumulated: list[str] = []
            while True:
                kind, value = stream_event_queue.get()
                if kind == QMSG_DONE:
                    break
                if kind == QMSG_ERROR:
                    yield ResponsesAgentStreamEvent(**self.create_text_delta(f"Error: {value}", "msg_1"))
                    break
                event: StreamEvent = value
                if hasattr(event, "data") and hasattr(event.data, "delta"):
                    delta = event.data.delta
                    accumulated.append(delta)
                    yield ResponsesAgentStreamEvent(**self.create_text_delta(delta, "msg_1"))

            task_future.result()

        yield ResponsesAgentStreamEvent(
            type="response.output_item.done",
            item=self.create_text_output_item(text="".join(accumulated), id="msg_1"),
        )


# ---------------------------------------------------------------------------
# MLflow model registration
# ---------------------------------------------------------------------------
nps_responses_agent = NPSResponsesAgent()
mlflow.openai.autolog()
set_model(nps_responses_agent)


# ---------------------------------------------------------------------------
# MLflow AgentServer  (Provides HTTP API that supports SSE via FastAPI)
# ---------------------------------------------------------------------------
agent_server = AgentServer("ResponsesAgent")


@invoke()
async def handle_invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    return await anyio.to_thread.run_sync(nps_responses_agent.predict, request)


@stream()
async def handle_stream(request: ResponsesAgentRequest) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    _DONE = object()
    event_generator = nps_responses_agent.predict_stream(request)
    try:
        while True:
            responses_agent_event = await anyio.to_thread.run_sync(next, event_generator, _DONE)
            if responses_agent_event is _DONE:
                break
            yield responses_agent_event
    finally:
        event_generator.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(agent_server.app, host=args.host, port=args.port)
