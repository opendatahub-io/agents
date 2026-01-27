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
   
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_key
   NPS_API_KEY=your_nps_key
   ```
   
   Then export them:
   ```bash
   export OPENAI_API_KEY=your_key
   export NPS_API_KEY=your_nps_key
   ```
   
   Get a free NPS API key at https://www.nps.gov/subjects/developer/get-started.htm

4. **Run the notebooks**
   - `nps_agent/nps_agent.ipynb` - Chat mode agent
   - `log_monitor/log_monitor_agent.ipynb` - Event-driven agent

5. **View traces in MLflow UI**
   ```bash
   mlflow ui --port 5001
   ```

## Project Structure

```
├── nps_agent/
│   ├── nps_agent.ipynb      # Chat agent notebook
│   ├── nps_mcp_server.py    # MCP server for NPS API
│   └── readme.md
├── log_monitor/
│   ├── log_monitor_agent.ipynb  # Event-driven agent notebook
│   ├── log_monitor_agent/       # Agent package
│   └── README.md
├── requirements.txt
└── readme.md
```
