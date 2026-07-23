import os
import shutil
import argparse
from collections.abc import AsyncGenerator

import uvicorn

from dotenv import load_dotenv

import mlflow
from mlflow.genai.agent_server import AgentServer, invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    create_text_delta,
    create_text_output_item,
)

from openai import AsyncClient
from agents import Agent, Runner, StreamEvent
from agents.mcp import MCPServerStdio
from agents.models.openai_provider import OpenAIChatCompletionsModel


# ---------------------------------------------------------------------------
# Load .env and define runtime constants
# ---------------------------------------------------------------------------
load_dotenv()
UV_EXE = shutil.which("uv")
if UV_EXE is None:
    raise ValueError("Requires 'uv' executable for MCP server environment management.")

MCP_ARGS = ["run", "fastmcp", "run", "./nps_mcp_server.py"]
MCP_ENV = {**os.environ, "NPS_API_KEY": os.environ.get("NPS_API_KEY", "DEMO_KEY")}
MCP_PARAMS = {"command": UV_EXE, "args": MCP_ARGS, "env": MCP_ENV}
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "EMPTY")
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


async def run_nps_agent(prompt) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    async with MCPServerStdio(params=MCP_PARAMS) as mcp_server:
        # Configure OpenAI-compatible endpoint
        async with AsyncClient(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY) as async_client:

            # Create the agent
            agent = Agent(
                name=AGENT_NAME,
                instructions=AGENT_INSTRUCTIONS,
                mcp_servers=[mcp_server],
                model=OpenAIChatCompletionsModel(model=OPENAI_MODEL_NAME, openai_client=async_client)
            )

            # Run the agent
            result = await Runner.run(agent, prompt)
            return result.final_output


async def run_streaming_nps_agent(prompt) -> AsyncGenerator[StreamEvent, None]:
    """Run the NPS agent with MCP tools and stream the text response."""
    async with MCPServerStdio(params=MCP_PARAMS) as mcp_server:
        # Configure OpenAI-compatible endpoint
        async with AsyncClient(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY) as async_client:

            # Create the agent
            agent = Agent(
                name=AGENT_NAME,
                instructions=AGENT_INSTRUCTIONS,
                mcp_servers=[mcp_server],
                model=OpenAIChatCompletionsModel(model=OPENAI_MODEL_NAME, openai_client=async_client)
            )

            # Run the agent with streaming
            streaming_result = Runner.run_streamed(agent, prompt)
            async for event in streaming_result.stream_events():
                yield event


# ---------------------------------------------------------------------------
# MLflow AgentServer  (Provides HTTP API that supports SSE via FastAPI)
# ---------------------------------------------------------------------------
mlflow.openai.autolog()
agent_server = AgentServer("ResponsesAgent")


@invoke()
async def handle_invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:

    result = await run_nps_agent(request.input)
    return ResponsesAgentResponse(output=[create_text_output_item(text=result, id="msg_1")])


@stream()
async def handle_stream(request: ResponsesAgentRequest) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:

    accumulated: list[str] = []
    async for event in run_streaming_nps_agent(request.input):

        if hasattr(event, "data") and hasattr(event.data, "delta"):
            delta = event.data.delta
            accumulated.append(delta)
            yield ResponsesAgentStreamEvent(**create_text_delta(delta, "msg_1"))

    yield ResponsesAgentStreamEvent(
        type="response.output_item.done",
        item=create_text_output_item(text="".join(accumulated), id="msg_1"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(agent_server.app, host=args.host, port=args.port)
