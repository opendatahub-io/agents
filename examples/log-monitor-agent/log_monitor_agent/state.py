"""Agent state definition for the workflow.

The AgentState TypedDict defines all data that flows through the LangGraph
workflow. Each node can read from and write to this shared state.
"""

from typing import TypedDict


class AgentState(TypedDict):
    """State passed through the agent workflow.

    Attributes:
        log_message: Raw log text from deployed server (input).
        classification: Classification result - "error", "warning", or "normal".
        diagnosis: Root cause analysis text.
        severity: Severity level - "high" or "low".
        action_taken: Final action - "slack_alert", "github_ticket", or "none".
    """

    log_message: str
    classification: str
    diagnosis: str
    severity: str
    action_taken: str
