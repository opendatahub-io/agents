# NPS Agent with MLflow Tracing

A sample AI agent that queries the National Parks Service using multiple tools, with full observability and evaluation via MLflow.

The agent and MCP server are based on: https://github.com/The-AI-Alliance/llama-stack-examples/blob/main/notebooks/01-responses/README_NPS.md

## What This Demonstrates

- **Agent with multiple tools** - Uses MCP to access NPS API tools (search_parks, get_park_events, get_park_alerts, etc.)
- **Chat mode** - Takes user messages, responds with formatted answers
- **MLflow tracing** - Full execution traces captured for debugging and analysis
- **Agent-as-a-Judge** - Automated evaluation of agent responses using an LLM judge

## Architecture

```
User Query → LlamaStack → MCP Server → NPS API
                ↓
           MLflow Trace
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
   ```bash
   export OPENAI_API_KEY=your_key
   ```

4. **Run the notebook**
   Open `nps_agent.ipynb` and run all cells

5. **View traces in MLflow UI**
   ```bash
   mlflow ui --port 5001
   ```
   Then open http://localhost:5001
