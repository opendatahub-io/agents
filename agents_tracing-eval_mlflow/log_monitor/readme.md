# Log Monitor Agent with MLflow Tracing

An event-driven agent that monitors server logs using LangGraph, with full observability and evaluation via MLflow.

The agent is based on: https://github.com/jwm4/agents/tree/001-log-monitor-agent/examples/log-monitor-agent

**What we added:** MLflow tracing and Agent-as-a-Judge evaluation to demonstrate observability and automated evaluation of agent execution.

## What This Demonstrates

- **Event-driven agent** - Processes log messages through a LangGraph workflow
- **MCP research tools** - Uses DeepWiki and Context7 for documentation lookup during diagnosis
- **MLflow tracing** - Full execution traces captured for every workflow step
- **Agent-as-a-Judge** - Automated evaluation of agent performance using an LLM judge

## Architecture

```
Log Message → Classify → Diagnose → Assess Severity → Route Action
                           ↓
                    MCP Tools (DeepWiki, Context7)
                           ↓
                      MLflow Trace
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
   ```bash
   export OPENAI_API_KEY=your_key
   ```

3. **Run the notebook**
   Open `log_monitor_agent.ipynb` and run all cells

4. **View traces in MLflow UI**
   ```bash
   mlflow ui --port 5001
   ```
   Then open http://localhost:5001

