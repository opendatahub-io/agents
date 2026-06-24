"""Tool implementations for the Log Monitor Agent.

This module provides:
- MCP-based research tools (Deep Wiki, Context7) for diagnosis
- Stub action tools (Slack, GitHub) for educational purposes

MCP Tools:
    - deepwiki: Structured, summarized docs with architectural insights for GitHub
      repositories. Also provides Q&A-style LLM chat.
    - context7: Real-time retrieval providing up-to-date, version-specific library
      docs and code snippets for git repos, OpenAPI specs, llms.txt files, or websites.

Action Tools (stubs):
    - send_slack_alert: Send alert to SRE (high severity)
    - check_existing_github_issue: Check for existing issues (low severity)
    - create_github_issue: Create new issue (low severity)
"""

import asyncio
import os
from typing import Optional

from langchain_mcp_adapters.client import MultiServerMCPClient


# =============================================================================
# MCP Client Configuration
# =============================================================================

# MCP server URLs
DEEPWIKI_MCP_URL = os.getenv("DEEPWIKI_MCP_URL", "https://mcp.deepwiki.com/mcp")
CONTEXT7_MCP_URL = os.getenv("CONTEXT7_MCP_URL", "https://mcp.context7.com/mcp")

# Global MCP client and tools cache
_mcp_client: Optional[MultiServerMCPClient] = None
_mcp_tools: Optional[list] = None


async def _init_mcp_client() -> MultiServerMCPClient:
    """Initialize the MCP client with DeepWiki and Context7 servers.

    Returns:
        Configured MultiServerMCPClient instance.
    """
    client = MultiServerMCPClient(
        {
            "deepwiki": {
                "url": DEEPWIKI_MCP_URL,
                "transport": "streamable_http",
            },
            "context7": {
                "url": CONTEXT7_MCP_URL,
                "transport": "streamable_http",
            },
        }
    )
    return client


async def _get_mcp_tools_async() -> list:
    """Get MCP tools from DeepWiki and Context7 servers (async).

    Returns:
        List of LangChain-compatible tools from MCP servers.
    """
    global _mcp_client, _mcp_tools

    if _mcp_tools is not None:
        return _mcp_tools

    print("[MCP] Connecting to research tools...")
    print(f"[MCP]   - DeepWiki: {DEEPWIKI_MCP_URL}")
    print(f"[MCP]   - Context7: {CONTEXT7_MCP_URL}")

    _mcp_client = await _init_mcp_client()
    _mcp_tools = await _mcp_client.get_tools()

    tool_names = [t.name for t in _mcp_tools]
    print(f"[MCP] Available tools: {tool_names}")

    return _mcp_tools


def get_mcp_tools() -> list:
    """Get MCP tools from DeepWiki and Context7 servers (sync wrapper).

    This function provides a synchronous interface to the async MCP client.
    Tools are cached after first initialization.

    Returns:
        List of LangChain-compatible tools from MCP servers.

    Example:
        tools = get_mcp_tools()
        llm_with_tools = llm.bind_tools(tools)
    """
    try:
        asyncio.get_running_loop()
        # If we're already in an async context, run in a thread pool
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _get_mcp_tools_async()).result()
    except RuntimeError:
        # No running loop, we can use asyncio.run directly
        return asyncio.run(_get_mcp_tools_async())


def get_research_tool_guidance() -> str:
    """Get guidance for the LLM on when to use research tools.

    Returns:
        String with tool usage guidance for inclusion in prompts.
    """
    return """
You have access to research tools that can help diagnose issues:

- **context7**: Use for real-time retrieval of up-to-date, version-specific
  library docs and code snippets. Good for looking up specific error messages,
  API documentation, or code patterns from git repos, OpenAPI specs, or websites.

- **deepwiki**: Use for structured, summarized documentation and architectural
  insights about GitHub repositories. Good for understanding how a library or
  framework works, getting Q&A-style explanations, or finding source code references.

Use these tools when:
- The error message references a specific library or framework
- You need current documentation to understand an API or configuration
- The issue requires understanding architectural patterns or best practices
- Looking up specific error codes or exception types

You may choose NOT to use these tools if:
- The issue is straightforward (e.g., obvious syntax error, clear resource exhaustion)
- The diagnosis is clear from the error message alone
"""


# =============================================================================
# Action Tools (Stubs for educational purposes)
# =============================================================================


def send_slack_alert(message: str, severity: str, diagnosis: str) -> None:
    """Send alert to SRE via Slack (STUB implementation).

    This is a STUB that prints a log message. In production, this would
    integrate with the Slack API to send actual alerts.

    Args:
        message: Alert message for SRE.
        severity: Severity level.
        diagnosis: Problem diagnosis.
    """
    print(f"STUB: Would send Slack alert to SRE: {message}")
    print(f"STUB: Severity: {severity}")
    print(f"STUB: Diagnosis: {diagnosis}")
    # TODO: Actual Slack API integration would go here
    # Example:
    # from slack_sdk import WebClient
    # client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    # client.chat_postMessage(
    #     channel="#sre-alerts",
    #     text=f":rotating_light: *{severity.upper()} Severity Alert*\n{message}\n\nDiagnosis: {diagnosis}"
    # )


def check_existing_github_issue(query: str) -> bool:
    """Check if a GitHub issue already exists for this problem (STUB).

    This is a STUB that always returns False. In production, this would
    search GitHub issues for duplicates.

    Args:
        query: Search query for existing issues.

    Returns:
        False (stub always returns False to trigger issue creation).
    """
    print(f"STUB: Checking for existing GitHub issue: {query}")
    print("STUB: No existing issue found (stub always returns False)")
    # TODO: Actual GitHub API integration would go here
    # Example:
    # from github import Github
    # g = Github(os.environ["GITHUB_TOKEN"])
    # repo = g.get_repo("org/repo")
    # issues = repo.get_issues(state="open")
    # for issue in issues:
    #     if query.lower() in issue.title.lower():
    #         return True
    # return False
    return False


def create_github_issue(title: str, body: str) -> None:
    """Create a new GitHub issue (STUB implementation).

    This is a STUB that prints a log message. In production, this would
    create an actual GitHub issue via the API.

    Args:
        title: Issue title.
        body: Issue description.
    """
    print(f"STUB: Would create GitHub issue: {title}")
    print(f"STUB: Issue body preview: {body[:100]}...")
    # TODO: Actual GitHub API integration would go here
    # Example:
    # from github import Github
    # g = Github(os.environ["GITHUB_TOKEN"])
    # repo = g.get_repo("org/repo")
    # repo.create_issue(title=title, body=body, labels=["auto-generated", "log-monitor"])
