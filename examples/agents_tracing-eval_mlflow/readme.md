# MLflow Agent Tracing & Evaluation

This repository demonstrates MLflow tracing and Agent-as-a-Judge evaluation capabilities with two different types of agents.

## Goals

1. **Chat Mode Agent (NPS Agent)** - An agent that takes user messages and responds with text, using multiple tools via MCP.

2. **Event-Driven Agent (Log Monitor Agent)** - An agent that takes structured events (log messages) and performs actions, but doesn't return a text response.

Both agents are configured to send tracing information to MLflow and use Agent-as-a-Judge for automated evaluation.

## Agents

### NPS Agent (`nps_agent/`)

A conversational agent that queries the National Parks Service API.

- **Mode**: Chat (user query → text response)
- **Tools**: MCP server with NPS API tools (search_parks, get_park_events, get_park_alerts, etc.)
- **LLM**: Llama Stack → OpenAI
- **Source**: [llama-stack-examples](https://github.com/The-AI-Alliance/llama-stack-examples/blob/main/notebooks/01-responses/README_NPS.md)

### Log Monitor Agent (`log_monitor/`)

An event-driven agent that processes server logs and routes alerts.

- **Mode**: Event-driven (log message → action taken)
- **Tools**: MCP research tools (DeepWiki, Context7) + action stubs (Slack, GitHub)
- **LLM**: Llama Stack → OpenAI via LangGraph
- **Source**: [jwm4/agents](https://github.com/jwm4/agents/tree/001-log-monitor-agent/examples/log-monitor-agent)

## What We Added

Both agents were enhanced with:

1. **MLflow Tracing** - `@mlflow.trace` decorators and `mlflow.start_span` calls to capture full execution traces
2. **Agent-as-a-Judge** - Automated evaluation using MLflow's `make_judge` with the `{{ trace }}` template

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Llama Stack server** on port 8321

3. **Set environment variables**
   
   Create a `.env` file in this directory (`agents_tracing-eval_mlflow/.env`):
   ```
   OPENAI_API_KEY=your_key
   NPS_API_KEY=your_nps_key
   ```
   
   Get a free NPS API key at https://www.nps.gov/subjects/developer/get-started.htm

4. **Run the notebooks** (choose MLflow native or OpenTelemetry for each agent)
   - `nps_agent/nps_agent.ipynb` - Chat agent (MLflow native)
   - `nps_agent/nps_otel.ipynb` - Chat agent (OpenTelemetry)
   - `log_monitor/log_monitor_agent.ipynb` - Event-driven agent (MLflow native)
   - `log_monitor/log_monitor_agent_otel.ipynb` - Event-driven agent (OpenTelemetry)


5. **View traces in MLflow UI**
   ```bash
   # For MLflow native notebooks:
   mlflow ui --port 5001
   # For OTel notebooks (server already running):
   # Open http://localhost:5002
   ```

## Project Structure

```
├── nps_agent/
│   ├── nps_agent.ipynb        # Chat agent notebook (MLflow native)
│   ├── nps_otel.ipynb         # Chat agent notebook (OpenTelemetry)
│   ├── nps_mcp_server.py      # MCP server for NPS API
│   └── readme.md
├── log_monitor/
│   ├── log_monitor_agent.ipynb      # Event-driven agent notebook (MLflow native)
│   ├── log_monitor_agent_otel.ipynb # Event-driven agent notebook (OpenTelemetry)
│   ├── log_monitor_agent/           # Agent package (MLflow native)
│   ├── log_monitor_agent_otel/      # Agent package (OpenTelemetry)
│   └── readme.md
├── requirements.txt
└── readme.md
```
## MLflow Native vs OpenTelemetry SDK: Analysis

We implemented both tracing approaches for each agent and compared the results.

### How We Tested

We ran all 20 log message examples through both the MLflow native and OTel notebooks and compared the traces and evaluation results side by side.

### What We Found

Both approaches produce **functionally equivalent results** — the Agent-as-a-Judge evaluations return similar (not identical) ratings and rationale across both tracing backends. Results are not perfectly identical perhaps due to LLM non-determinism, but the overall quality and patterns are consistent.


### UI Differences

The trace detail views are very similar between the two approaches. Both show the full span hierarchy, inputs/outputs for each span, and Agent-as-a-Judge assessments in the side panel.

Minor differences:
- **Data organization**: The way trace data is structured and displayed differs slightly between native and OTel traces (e.g., how inputs/outputs are grouped, field ordering).
- **Span icons and symbols**: The MLflow UI uses different icons and symbols for native spans vs OTel-ingested spans.
- **Span nesting**: OTel traces may have an extra root span wrapping the agent workflow, since the OTel instrumentation adds an explicit parent span.


## Updates (01/29/2026)
> **Note:** MLflow 3.9.0 introduced a [Judge Builder UI](https://www.linkedin.com/posts/mlflow-org_mlflow-genai-llmops-activity-7422683289041244160-yTOU) that lets you define and iterate on custom LLM judge prompts directly from the UI. You can create prompts, test-run them on your traces, and then use them for online monitoring or via the Python SDK. This is an alternative to defining judges in code as shown in these notebooks.
