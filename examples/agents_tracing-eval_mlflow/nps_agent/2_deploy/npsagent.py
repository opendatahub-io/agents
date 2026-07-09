import asyncio
import os
import argparse

import uvicorn

import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

import mlflow
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from mlflow.genai.agent_server import AgentServer, invoke

from openai import AsyncClient
from agents import Agent, Runner, set_default_openai_client
from agents.mcp import MCPServerStdio

# ---------------------------------------------------------------------------
# Create an NPS Agent  (same pattern as 1_develop/2_evaluate.ipynb)
# ---------------------------------------------------------------------------
AGENT_INSTRUCTIONS = (
    "You are a helpful National Parks Service assistant. "
    "Use the available tools to answer questions about national parks, "
    "events, activities, campgrounds, and visitor information. "
)


async def run_nps_agent(prompt) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    command = "uv"
    args = ["run", "fastmcp", "run", "./nps_mcp_server.py"]
    env = {**os.environ, "NPS_API_KEY": os.environ.get("NPS_API_KEY", "")}
    async with MCPServerStdio(params={"command": command, "args": args, "env": env}) as mcp_server:
        # Configure OpenAI-compatible endpoint
        async_client = AsyncClient(
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
        set_default_openai_client(client=async_client)

        # Create the agent
        agent = Agent(
            name="NPS Agent",
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model=os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
        )

        # Run the agent
        result = await Runner.run(agent, prompt)
        return result.final_output


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent — wraps run_nps_agent to provide tracing
# ---------------------------------------------------------------------------
class NPSResponsesAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        try:
            result = asyncio.run(run_nps_agent(request.input))
        except Exception as e:
            result = f"Error: {e}"
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=result, id="msg_1")]
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
def handle_invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    return nps_responses_agent.predict(request)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(agent_server.app, host=args.host, port=args.port)
