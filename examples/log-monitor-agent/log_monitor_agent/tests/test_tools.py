"""Tests for tool implementations.

These tests verify that:
- MCP tool configuration is correct
- Stub action tools behave correctly
"""


# =============================================================================
# MCP Research Tool Configuration Tests
# =============================================================================


class TestMCPToolConfiguration:
    """Tests for MCP tool configuration."""

    def test_mcp_server_urls_have_defaults(self):
        """Test that MCP server URLs have sensible defaults."""
        from log_monitor_agent.tools import DEEPWIKI_MCP_URL, CONTEXT7_MCP_URL

        assert DEEPWIKI_MCP_URL == "https://mcp.deepwiki.com/mcp"
        assert CONTEXT7_MCP_URL == "https://mcp.context7.com/mcp"

    def test_research_tool_guidance_content(self):
        """Test that research tool guidance includes both tools."""
        from log_monitor_agent.tools import get_research_tool_guidance

        guidance = get_research_tool_guidance()

        assert "context7" in guidance.lower()
        assert "deepwiki" in guidance.lower()
        assert "real-time retrieval" in guidance.lower()
        assert "structured" in guidance.lower()


# =============================================================================
# User Story 4: Slack Alert Tool Tests
# =============================================================================


class TestSlackAlertTool:
    """Tests for Slack alert stub tool (US4)."""

    def test_slack_stub_tool_invocation(self, capsys):
        """T028: Test Slack stub tool prints appropriate message."""
        from log_monitor_agent.tools import send_slack_alert

        send_slack_alert(
            message="High severity issue detected - Database down",
            severity="high",
            diagnosis="Database server is unreachable",
        )

        # Verify output
        captured = capsys.readouterr()
        assert "STUB: Would send Slack alert to SRE" in captured.out
        assert "High severity issue detected" in captured.out
        assert "high" in captured.out.lower()
        assert "Database server is unreachable" in captured.out


# =============================================================================
# User Story 5: GitHub Tool Tests
# =============================================================================


class TestGitHubTools:
    """Tests for GitHub stub tools (US5)."""

    def test_github_issue_check_stub_returns_false(self, capsys):
        """T033: Test GitHub issue check stub always returns False."""
        from log_monitor_agent.tools import check_existing_github_issue

        result = check_existing_github_issue(query="disk space warning")

        # Verify output
        captured = capsys.readouterr()
        assert "STUB: Checking for existing GitHub issue" in captured.out
        assert "disk space warning" in captured.out
        assert "always returns False" in captured.out

        # Verify return value (stub always returns False per spec)
        assert result is False

    def test_github_issue_create_stub(self, capsys):
        """T034: Test GitHub issue create stub prints message."""
        from log_monitor_agent.tools import create_github_issue

        create_github_issue(
            title="[Auto] WARNING: Disk space low on /var/log",
            body="## Log Message\nDisk space warning\n\n## Diagnosis\nLog rotation needed",
        )

        # Verify output
        captured = capsys.readouterr()
        assert "STUB: Would create GitHub issue" in captured.out
        assert "[Auto] WARNING: Disk space low" in captured.out
        assert "Issue body preview" in captured.out
