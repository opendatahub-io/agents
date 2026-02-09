# Log Monitor Agent with MLflow Tracing

An event-driven agent that monitors server logs using LangGraph, with full observability and evaluation via MLflow.

The agent is based on: https://github.com/jwm4/agents/tree/001-log-monitor-agent/examples/log-monitor-agent

**What we added:** MLflow tracing and Agent-as-a-Judge evaluation to demonstrate observability and automated evaluation of agent execution.

## What This Demonstrates

- **Event-driven agent** - Processes log messages through a LangGraph workflow
- **MCP research tools** - Uses DeepWiki and Context7 for documentation lookup during diagnosis
- **MLflow tracing** - Full execution traces captured for every workflow step
- **Agent-as-a-Judge** - Automated evaluation of agent performance using two LLM judges

## Choose a Notebook

Both notebooks run the same log monitor agent and evaluation — pick one based on the tracing approach you want:

| Notebook | Tracing Method | Description |
|----------|---------------|-------------|
| `log_monitor_agent.ipynb` | MLflow native (`@mlflow.trace`) | Uses MLflow's built-in tracing with a local SQLite backend |
| `log_monitor_agent_otel.ipynb` | OpenTelemetry (OTLP export) | Uses OTel SDK to create spans, exported to MLflow server via OTLP/HTTP |

**Option A — MLflow Native** (`log_monitor_agent.ipynb`): Uses `@mlflow.trace` decorators and `mlflow.start_span()` to capture traces directly into a local SQLite database. No server required.

**Option B — OpenTelemetry** (`log_monitor_agent_otel.ipynb`): Uses the OpenTelemetry SDK (`TracerProvider`, `BatchSpanProcessor`, `OTLPSpanExporter`) to create spans and export them to an MLflow server over HTTP. Requires a running MLflow server. More portable and follows the OTel standard.

## Architecture

```
Log Message → Classify → Diagnose → Assess Severity → Route Action
                           ↓
                    MCP Tools (DeepWiki, Context7)
                           ↓
              OTel Spans / MLflow Trace
                           ↓
                 OTLP/HTTP → MLflow Server  (OTel)
                 or SQLite (MLflow native)
                           ↓
              Agent-as-a-Judge (evaluates trace)
```

**Workflow:**
1. **Classify** - error/warning/normal
2. **Diagnose** - root cause analysis (uses MCP tools for documentation lookup)
3. **Assess Severity** - high/low
4. **Route** - Slack alert (high) or GitHub ticket (low)

## Quick Start

1. **Start LlamaStack server** on port 8321

2. **Set OpenAI API key** (for Agent-as-a-Judge)

   Make sure `OPENAI_API_KEY` is set in the `.env` file in the parent directory (`agents_tracing-eval_mlflow/.env`):
   ```
   OPENAI_API_KEY=your_key
   ```

3. **Run either notebook**

   **Option A — MLflow Native** (`log_monitor_agent.ipynb`):
   Open and run all cells. Traces are saved to a local `mlflow.db` file.

   **Option B — OpenTelemetry** (`log_monitor_agent_otel.ipynb`):
   First start an MLflow server:
   ```bash
   mlflow server --backend-store-uri sqlite:///mlflow.db --port 5001
   ```
   Then open and run all cells. View traces at http://localhost:5001.

