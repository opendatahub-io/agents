# LangGraph Agent with MLflow Tracing

A sample AI agent built with LangGraph that queries the National Parks Service, with automatic tracing via `mlflow.langchain.autolog()`.

## What This Demonstrates

- **ReAct Agent with LangGraph using NPS mcp** - A simple agent loop using LangGraph's `StateGraph`

- **MLflow Auto-Tracing** - Automatic trace capture with `mlflow.langchain.autolog()` (single graph invocation builds one trace )
- **Tracing conversation** - Using LangGraph's thread IDs or manually with `@mlflow.trace` decorator to view a group of traces as a session in the UI

## Prerequisites

1. **Python 3.12+** (recommended via `uv`)
2. **NPS MCP Server** running on `localhost:3005` (see `nps_mcp_server.py` in this folder)
3. **OpenAI API Key** set in `.env`

## Quick Start

### 1. Install Dependencies

From the parent directory (`agents_tracing-eval_mlflow/`):
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

set `OPENAI_API_KEY` in the parent directory's `.env` file (`agents_tracing-eval_mlflow/.env`):

### 3. NPS MCP Server

Start the MCP server from this folder:
```bash
python nps_mcp_server.py --transport sse --port 3005
```

### 4. Run the Notebook

Open and run `Nps_agent_langchain_autolog.ipynb` in Jupyter.

### 5. View Traces in MLflow UI

After running the notebook, start the MLflow UI from this directory to view traces:

```bash
mlflow ui --port 5001 --backend-store-uri sqlite:///mlflow.db
```

Then open http://localhost:5001 in your browser.

## References

- [MLflow LangGraph Integration](https://mlflow.org/docs/latest/genai/tracing/integrations/listing/langgraph/)
- [MLflow User & Session Tracking](https://mlflow.org/docs/latest/genai/tracing/track-users-sessions/)
- [LangChain MCP Integration](https://python.langchain.com/docs/integrations/tools/mcp/)
- [OpenAI Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/) (related example using OpenAI SDK)
