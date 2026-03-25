# ODH Agents Experimental Repository

Experimental sandbox for the OpenDataHub community to explore agentic AI reasoning. Apache 2.0 licensed. **Not production code** -- APIs, examples, and tooling may break without notice.

## What This Is

A collection of examples, tools, and validation notebooks demonstrating how to build AI agents that use external tools via the **Model Context Protocol (MCP)**. The repo intentionally does NOT provide a custom SDK or agent framework (see `adr/minimal-sdk.md` for the "Option 8" decision). Instead, it shows multiple approaches:

1. **Direct OpenAI SDK** (Python & Go) -- calling `client.responses.create()` with MCP tool definitions (simplest examples)
2. **LangChain + LangGraph** -- multi-agent workflows with state machines, structured outputs, conditional routing, and guardrails
3. **CrewAI** -- multi-agent crews with sequential/hierarchical task execution
4. **FastMCP** -- building custom MCP servers (e.g., NPS API server)
5. **MLflow + OpenTelemetry** -- tracing and Agent-as-a-Judge evaluation

## Tech Stack

- **Languages**: Python 3.13+ (primary), Go 1.24 (secondary)
- **LLM Clients**: `openai` Python SDK, `openai-go` Go SDK, `langchain-openai` (`ChatOpenAI`)
- **Agent Frameworks**: LangGraph (`StateGraph`, conditional edges, structured output), CrewAI (`@CrewBase`, agents/tasks YAML config), LangChain (tool binding, `MultiServerMCPClient`, PIIMiddleware guardrails)
- **MCP Servers**: FastMCP (custom server authoring), `kubernetes-mcp-server`, GitHub Copilot MCP, Slack MCP, ServiceNow MCP, Google Workspace MCP, Jira MCP (Atlassian), DeepWiki MCP, Context7 MCP
- **Inference**: vLLM (self-hosted, tool calling with `--enable-auto-tool-choice`), Ollama (local models), OpenAI API, Google Gemini API, IBM WatsonX
- **API Layer**: Llama Stack (OpenAI-compatible Responses API proxy), can also call OpenAI/vLLM directly
- **Tracing/Eval**: MLflow (`@mlflow.trace`, Agent-as-a-Judge), OpenTelemetry
- **Benchmarking**: BFCL (Berkeley Function Calling Leaderboard), bootstrap significance testing (numpy, scipy, tqdm)
- **Web/Infra**: Flask, Kubernetes Python client, Podman/Docker, Pydantic (structured outputs)
- **Models tested**: GPT-4o, GPT-4o-mini, Qwen3-0.6B/1.7B/8B, Llama 3.2, Llama Guard 3, GPT-OSS-20b/120b, Gemini 2.5 Pro

## Key Directories

```
examples/
  github-mcp/          # Simplest example: OpenAI SDK + GitHub MCP (Python & Go)
  gsuite-mcp/          # Google Docs MCP with full OAuth2 flow (PKCE in Go)
  kubernetes-mcp/      # K8s pod listing with bearer token auth + RBAC demo manifests
  slack-mcp/           # Slack channel listing + Podman MCP server setup + OAuth scope validation
  servicenow-mcp/      # ServiceNow incident listing
  mcp-project-reporting/  # Jira MCP via docker-compose + complex Llama Stack config (OAuth2, scoring, eval)
  langchain-langgraph/ # Full app: Flask UI + LangGraph multi-stage routing (classify -> support/legal -> K8s/GitHub MCP)
  ai_assistant_for_troubleshooting_apps/  # CrewAI: K8s event watcher -> diagnose -> GitHub PR -> Slack notify
  agents_tracing-eval_mlflow/  # MLflow tracing examples: NPS chat agent + log monitor event-driven agent
tools/
  mcp-tester/          # MCP server connectivity validator (auto-detects SSE vs HTTP transport)
  llama-stack/local/   # Local Llama Stack quickstart (setup.sh + run.yaml)
  vllm/                # vLLM setup for macOS (CPU, Qwen3-0.6B)
benchmarking/          # BFCL benchmarking guide + significance testing (bootstrap, permutation)
validation-vllm/       # Jupyter notebooks validating GPT-OSS models (function calling, web search, file search)
migration/             # Legacy agent migration from WatsonX (notebook + run.yaml)
adr/                   # Architecture Decision Records (template + minimal-sdk decision)
mcp-discovery-configmap/  # JSON schema for K8s ConfigMap-based MCP server discovery
```

## Important Files

- `adr/minimal-sdk.md` -- Key architectural decision: why no custom SDK (Option 8)
- `examples/langchain-langgraph/workflow.py` -- Most complex example: LangGraph StateGraph with classification, routing, K8s + GitHub MCP calls
- `examples/ai_assistant_for_troubleshooting_apps/crew.py` -- CrewAI multi-agent crew with 3 MCP servers
- `examples/agents_tracing-eval_mlflow/nps_agent/nps_mcp_server.py` -- Custom FastMCP server (NPS API, 758 lines)
- `examples/agents_tracing-eval_mlflow/log_monitor/log_monitor_agent/agent.py` -- LangGraph workflow with MLflow tracing
- `tools/mcp-tester/test-mcp-server.py` -- MCP server diagnostic tool
- `mcp-discovery-configmap/schema.json` -- MCP ConfigMap schema (url, transport, description, logo)
- `benchmarking/significance-testing/significance_test.py` -- BFCL statistical comparison CLI

## Common Setup Patterns

**Direct vLLM + OpenAI SDK** (simplest):
```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY
python example.py  # or: go run example.go
```

**Via Llama Stack** (most examples):
```bash
llama stack run run.yaml --image-type venv   # starts on port 8321
export OPENAI_BASE_URL=http://localhost:8321/v1/openai/v1
```

**Via OpenAI directly** (github-mcp, gsuite-mcp defaults):
```bash
export OPENAI_API_KEY=sk-...
export INFERENCE_MODEL=openai/gpt-4o
```

**Via Ollama** (langchain-langgraph):
```bash
ollama pull llama-guard3:1b && ollama serve
export INFERENCE_MODEL=ollama/llama3.2:3b
```

Service-specific tokens: `GITHUB_TOKEN`, `SLACK_MCP_TOKEN`, `KUBE_TOKEN`, `GOOGLE_OAUTH_CLIENT_ID`/`SECRET`, `NPS_API_KEY`

## Conventions

- Each example is self-contained with its own README, dependencies (`pyproject.toml` / `go.mod`), and Llama Stack config (`run.yaml`)
- Python examples: `openai` SDK with `client.responses.create()` and MCP tool dicts
- Go examples: `openai-go` with `responses.ResponseNewParams` and `ToolMcpParam`
- MCP transports: SSE (`/sse` endpoint) or streamable HTTP (`/mcp` endpoint)
- Structured outputs via Pydantic models + `llm.with_structured_output()` (LangChain pattern)
- LangGraph state: `TypedDict` with `add_messages` annotation for message accumulation
- CrewAI config: YAML-based agent/task definitions in `config/` directory
- Package management: `uv` (Python), Go modules
- ADRs follow `adr/template.md` (Context -> Decision -> Status -> Consequences)
