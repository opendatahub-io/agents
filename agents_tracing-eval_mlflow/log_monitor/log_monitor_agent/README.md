# Log Monitor Agent with MLflow Tracing

An event-driven agent that monitors server logs using LangGraph, with full observability and evaluation via MLflow.

Based on: https://github.com/jwm4/agents/tree/001-log-monitor-agent/examples/log-monitor-agent

## What This Demonstrates

- **Event-driven agent** - Processes log events (vs chat-based NPS agent)
- **LangGraph workflow** - Multi-step: Classify → Diagnose → Assess → Route
- **MLflow tracing** - Full execution traces for debugging and analysis
- **Agent-as-a-Judge** - Automated evaluation of agent decisions

## Overview

This agent monitors server log messages and performs intelligent routing:

```
Log Message → Classify → Diagnose → Assess Severity → Take Action
                ↓           ↓              ↓
            error/warning  research    high → Slack Alert
            normal → END   tools       low  → GitHub Ticket
```

## Features

- **Log Classification**: Analyzes log messages to detect errors, warnings, or normal info
- **Problem Diagnosis**: Uses LLM to determine root cause with MCP research tools
- **Severity Assessment**: Determines if issue is high or low severity
- **Automated Routing**: High severity → SRE alert, Low severity → GitHub ticket

**MCP research tools** (DeepWiki, Context7) provide real documentation lookup.
**Slack and GitHub integrations** are stub implementations for educational purposes.

## Installation

```bash
cd examples/log-monitor-agent

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Configuration

Set environment variables based on your LLM backend:

```bash
# Option 1: Use Llama Stack (default)
export LLAMA_STACK_URL=http://localhost:8321
export MODEL_NAME=openai/gpt-4o  # optional, defaults to openai/gpt-4o

# Option 2: Use OpenAI directly
export USE_LLAMA_STACK=false
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-4o  # optional, defaults to gpt-4o
```

## Usage

### Command Line

```bash
# Process an error log
python -m log_monitor_agent "ERROR: Database connection failed - ConnectionRefusedError"

# Process a warning log
python -m log_monitor_agent "WARNING: Memory usage at 85%, approaching threshold"

# Process an informational log (no action taken)
python -m log_monitor_agent "INFO: Application started successfully"
```

### As a Python Module

```python
from log_monitor_agent import process_log_message

# Process any log message
process_log_message("ERROR: NullPointerException in UserService.java:142")
```

## Example Output

### High Severity Error

```
Input: ERROR: Database connection failed - ConnectionRefusedError
------------------------------------------------------------
[LLM] Using Llama Stack at http://localhost:8321
[LLM] Model: openai/gpt-4o
[Classify] Classification: error (confidence: 0.95)
[Classify] Indicators: ['ERROR', 'connection failed', 'ConnectionRefusedError']
[Diagnose] Analyzing root cause...
[MCP] Connecting to research tools...
[MCP]   - DeepWiki: https://mcp.deepwiki.com/mcp
[MCP]   - Context7: https://mcp.context7.com/mcp
[Diagnose] MCP research tools available
[Diagnose] Diagnosis: Database server is unreachable, likely network issue or server down
[Severity] Assessment: high (confidence: 0.88)
[Severity] Reasoning: Database connectivity affects all users
STUB: Would send Slack alert to SRE: High severity issue detected - Database server is unreachable
STUB: Severity: high
STUB: Diagnosis: Database server is unreachable
Action taken: slack_alert
```

### Low Severity Warning

```
Input: WARNING: Disk space low on /var/log
------------------------------------------------------------
[Classify] Classification: warning (confidence: 0.92)
[Classify] Indicators: ['WARNING', 'Disk space low']
[Diagnose] Analyzing root cause...
[Diagnose] Diagnosis: Log directory filling up, may need log rotation
[Severity] Assessment: low (confidence: 0.85)
[Severity] Reasoning: Disk space warning is not immediately critical
STUB: Checking for existing GitHub issue: Log directory filling up
STUB: No existing issue found (stub always returns False)
STUB: Would create GitHub issue: [Auto] WARNING: Disk space low on /var/log...
Action taken: github_ticket
```

## Architecture

```
log-monitor-agent/
├── pyproject.toml           # Package configuration
├── README.md
└── log_monitor_agent/       # Python package
    ├── __init__.py          # Package exports
    ├── __main__.py          # CLI entry point
    ├── agent.py             # LangGraph workflow definition
    ├── tools.py             # MCP research tools + stub action tools
    ├── schemas.py           # Pydantic schemas for LLM output
    ├── llm.py               # LLM configuration (Llama Stack / OpenAI toggle)
    ├── state.py             # AgentState TypedDict
    └── tests/
        ├── test_agent.py    # Workflow tests
        └── test_tools.py    # Tool tests
```

## Workflow Nodes

| Node | Purpose |
|------|---------|
| `classify` | Classify log as error/warning/normal |
| `diagnose` | Analyze root cause (with MCP research tools) |
| `assess_severity` | Determine high/low severity |
| `alert_sre` | Send Slack alert (high severity) |
| `manage_ticket` | Create GitHub issue (low severity) |

## Tools

### MCP Research Tools (Real Integrations)

The diagnosis step uses MCP (Model Context Protocol) tools for documentation lookup:

- **deepwiki** (`https://mcp.deepwiki.com/mcp`): Structured, summarized docs with
  architectural insights for GitHub repositories. Also provides Q&A-style LLM chat.
  Good for understanding how a library works or finding source code references.

- **context7** (`https://mcp.context7.com/mcp`): Real-time retrieval providing
  up-to-date, version-specific library docs and code snippets for git repos,
  OpenAPI specs, llms.txt files, or plain websites. Good for looking up specific
  error messages or API documentation.

The LLM decides whether to use these tools based on the complexity of the issue.

### Stub Action Tools

Action tools print educational output showing what production code would do:

- `send_slack_alert` - Alert SRE via Slack
- `check_existing_github_issue` - Check for duplicates
- `create_github_issue` - Create new issue

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agent.py
pytest tests/test_tools.py
```

## Extending This Example

### Adding Real Integrations

Replace stub action tools with actual API calls:

1. **Slack**: Use `slack_sdk` with `SLACK_BOT_TOKEN`
2. **GitHub**: Use `PyGithub` with `GITHUB_TOKEN`

### Configuring MCP Servers

MCP server URLs can be customized via environment variables:

```bash
export DEEPWIKI_MCP_URL=https://mcp.deepwiki.com/mcp
export CONTEXT7_MCP_URL=https://mcp.context7.com/mcp
```

### Customizing Classification

Modify `LogClassificationSchema` in `schemas.py` to add categories or adjust the classification prompt in `agent.py`.

### Adding More Severity Levels

Update `SeverityAssessmentSchema` and `route_by_severity` function to handle additional severity levels.

## License

See repository LICENSE file.
