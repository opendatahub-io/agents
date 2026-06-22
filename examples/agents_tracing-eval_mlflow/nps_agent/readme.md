# NPS Agent with MLflow Tracing

A sample AI agent that queries the National Parks Service using multiple tools, with full observability and evaluation via MLflow.

The agent and MCP server are based on: https://github.com/The-AI-Alliance/llama-stack-examples/blob/main/notebooks/01-responses/README_NPS.md

## What This Demonstrates

- **Agent with multiple tools** - Uses MCP to access NPS API tools (search_parks, get_park_events, get_park_alerts, etc.)
- **Chat mode** - Takes user messages, responds with formatted answers
- **MLflow tracing** - Full execution traces captured for debugging and analysis
- **Agent-as-a-Judge** - Automated evaluation of agent responses using an LLM judge

## Choose a Notebook

The first two notebooks run the same NPS agent and evaluation — pick one based on the tracing approach you want.
The remaining notebooks demonstrate alternative frameworks and judge configurations.

| Notebook | Tracing Method | Description |
|----------|----------------|-------------|
| `nps_agent.ipynb` | MLflow native (`@mlflow.trace`) | MLflow built-in tracing with a local SQLite backend |
| `nps_otel.ipynb` | OpenTelemetry (OTLP export) | OTel SDK spans exported to MLflow server via OTLP/HTTP |
| `nps_agent_openai_direct.ipynb` | MLflow native | Same agent using the OpenAI SDK directly instead of LlamaStack |
| `nps_agent_custom_judge.ipynb` | MLflow native | Custom judge provider; traces the judge's own LLM calls |
| `Nps_agent_langchain_autolog.ipynb` | MLflow autolog | LangGraph ReAct agent with automatic tracing, memory, and session tracking |

**Option A — MLflow Native** (`nps_agent.ipynb`): Uses `@mlflow.trace` decorators and `mlflow.start_span()` to capture traces directly into a local SQLite database. No server required.

**Option B — OpenTelemetry** (`nps_otel.ipynb`): Uses the OpenTelemetry SDK (`TracerProvider`, `BatchSpanProcessor`, `OTLPSpanExporter`) to create spans and export them to an MLflow server over HTTP. Requires a running MLflow server. More portable and follows the OTel standard.

**Option C — LangGraph with MLflow Autolog** (`Nps_agent_langchain_autolog.ipynb`): See [LangGraph README](langgraph-README.md) for details.

## Architecture

```
User Query → LlamaStack → MCP Server → NPS API
                ↓
       OTel Spans / MLflow Trace
                ↓
    OTLP/HTTP → MLflow Server  (OTel)
    or SQLite (MLflow native)
                ↓
       Agent-as-a-Judge (evaluates trace)
```

## Quick Start

1. **Start LlamaStack server** on port 8321

2. **Start NPS MCP server**
   ```bash
   python nps_mcp_server.py --transport sse --port 3005
   ```

3. **Set OpenAI API key** (for Agent-as-a-Judge)

   Make sure `OPENAI_API_KEY` is set in the parent directory's `.env` file (`agents_tracing-eval_mlflow/.env`):
   ```
   OPENAI_API_KEY=your_key
   ```

4. **Run a notebook**

   **Option A — MLflow Native** (`nps_agent.ipynb`):
   Open and run all cells. Traces are saved to a local `mlflow.db` file.

   **Option B — OpenTelemetry** (`nps_otel.ipynb`):
   First start an MLflow server:
   ```bash
   mlflow server --backend-store-uri sqlite:///mlflow.db --port 5001
   ```
   Then open and run all cells. View traces at http://localhost:5001.

   **Option C — LangGraph** (`Nps_agent_langchain_autolog.ipynb`):
   Open and run all cells. See [langgraph-README.md](langgraph-README.md) for full setup.

---

## End-to-End Lifecycle Tutorials

The subdirectories below walk through the full journey from local development to
production deployment and monitoring on RHOAI. By following these tutorials in
order you will learn how to:

- Instrument an agent for full observability over each action it takes
- Evaluate an agent during development to catch errors before they reach users
- Deploy an agent to production as an HTTP service and run inference against it
- Observe and evaluate production performance to catch behavioral drift

| Directory | Tutorial | Description |
|-----------|----------|-------------|
| [`1_develop/`](./1_develop/README.md) | Develop | Instrument and evaluate the agent locally using MLflow tracing and Agent-as-a-Judge |
| [`2_deploy/`](./2_deploy/README.md) | Deploy | Package and deploy the agent to RHOAI as an HTTP service via S2I build |
| [`3_observe/`](./3_observe/README.md) | Observe | Run outer-loop evaluations against the deployed agent in production |

Each tutorial stands on its own if you only want to learn about a specific stage.

### Prerequisites

**For `1_develop/`:**
- An OpenAI-compatible endpoint (OpenAI, vLLM, llama.cpp, Ollama, etc.)
- Space to run a local MLflow server (~5 MB)

**For `2_deploy/` and `3_observe/`:**
- An OpenAI-compatible endpoint accessible to your cluster
- RHOAI with the MLflow server enabled
- OpenShift CLI (`oc`)

### Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies for the stage you want
uv venv --python 3.12
uv pip install -r 1_develop/requirements.txt   # or 2_deploy/requirements.txt

# Configure environment variables
cp env.sample .env        # then edit .env with your API keys and settings
source .venv/bin/activate
```
