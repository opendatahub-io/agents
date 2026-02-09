# NPS Agent with MLflow Tracing

A sample AI agent that queries the National Parks Service using multiple tools, with full observability and evaluation via MLflow.

The agent and MCP server are based on: https://github.com/The-AI-Alliance/llama-stack-examples/blob/main/notebooks/01-responses/README_NPS.md

## What This Demonstrates

- **Agent with multiple tools** - Uses MCP to access NPS API tools (search_parks, get_park_events, get_park_alerts, etc.)
- **Chat mode** - Takes user messages, responds with formatted answers
- **MLflow tracing** - Full execution traces captured for debugging and analysis
- **Agent-as-a-Judge** - Automated evaluation of agent responses using an LLM judge

## Choose a Notebook

Both notebooks run the same NPS agent and evaluation — pick one based on the tracing approach you want:

| Notebook | Tracing Method | Description |
|----------|---------------|-------------|
| `nps_agent.ipynb` | MLflow native (`@mlflow.trace`) | Uses MLflow's built-in tracing with a local SQLite backend |
| `nps_otel.ipynb` | OpenTelemetry (OTLP export) | Uses OTel SDK to create spans, exported to MLflow server via OTLP/HTTP |

**Option A — MLflow Native** (`nps_agent.ipynb`): Uses `@mlflow.trace` decorators and `mlflow.start_span()` to capture traces directly into a local SQLite database. No server required.

**Option B — OpenTelemetry** (`nps_otel.ipynb`): Uses the OpenTelemetry SDK (`TracerProvider`, `BatchSpanProcessor`, `OTLPSpanExporter`) to create spans and export them to an MLflow server over HTTP. Requires a running MLflow server. More portable and follows the OTel standard.

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

   Make sure `OPENAI_API_KEY` is set in the `.env` file in the parent directory (`agents_tracing-eval_mlflow/.env`):
   ```
   OPENAI_API_KEY=your_key
   ```

4. **Run either notebook**

   **Option A — MLflow Native** (`nps_agent.ipynb`):
   Open and run all cells. Traces are saved to a local `mlflow.db` file.

   **Option B — OpenTelemetry** (`nps_otel.ipynb`):
   First start an MLflow server:
   ```bash
   mlflow server --backend-store-uri sqlite:///mlflow.db --port 5001
   ```
   Then open and run all cells. View traces at http://localhost:5001.
