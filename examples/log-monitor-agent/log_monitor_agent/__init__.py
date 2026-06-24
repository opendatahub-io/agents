"""Log Monitor Agent - Educational example demonstrating LangChain/LangGraph patterns.

This agent monitors server log messages and:
1. Classifies them as error/warning/normal
2. Diagnoses problems using optional research tools
3. Assesses severity (high/low)
4. Routes to appropriate action (Slack alert or GitHub ticket)

All external integrations are stub implementations for educational purposes.
"""

from .agent import process_log_message

__all__ = ["process_log_message"]
