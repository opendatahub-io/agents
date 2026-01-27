"""Log Monitor Agent - Main workflow definition with MLflow tracing.

This module implements the LangGraph workflow for log monitoring:
1. Classify log messages as error/warning/normal
2. Diagnose problems (with MCP research tools: DeepWiki, Context7)
3. Assess severity (high/low)
4. Route to appropriate action (Slack alert or GitHub ticket)

MCP tools provide real documentation lookup capabilities.
Slack and GitHub integrations are stub implementations for educational purposes.

MLflow tracing captures the full execution for observability and evaluation.
"""

import os
import mlflow
from mlflow.entities import SpanType

from langgraph.graph import StateGraph, END

from .state import AgentState
from .llm import get_llm
from .schemas import LogClassificationSchema, SeverityAssessmentSchema

# MLflow setup
db_path = os.path.join(os.path.dirname(__file__), "..", "mlflow.db")
mlflow.set_tracking_uri(f"sqlite:///{os.path.abspath(db_path)}")
mlflow.set_experiment("log-monitor-agent")


# =============================================================================
# Node Functions
# =============================================================================


@mlflow.trace(name="classify_log", span_type=SpanType.LLM)
def classify_log(state: AgentState) -> dict:
    """Classify a log message as error, warning, or normal.

    This node uses the LLM to analyze the log message content and determine
    its classification. The LLM returns structured output using
    LogClassificationSchema.

    Args:
        state: Current agent state with log_message.

    Returns:
        Updated state with classification field.
    """
    log_message = state["log_message"]

    # Handle empty or malformed logs - treat as normal (per spec edge case)
    if not log_message or not log_message.strip():
        print("[Classify] Empty log message - treating as normal")
        return {"classification": "normal"}

    llm = get_llm()
    structured_llm = llm.with_structured_output(LogClassificationSchema)

    prompt = f"""Analyze this server log message and classify it.

Log message: {log_message}

Determine if this is an error, warning, or normal informational message.
Look for indicators like:
- ERROR, FAIL, Exception, stack traces → error
- WARNING, WARN, threshold, approaching limit → warning
- INFO, DEBUG, success, started, completed → normal

Provide your classification with confidence score and the indicators you found."""

    result = structured_llm.invoke(prompt)

    print(f"[Classify] Classification: {result.classification} (confidence: {result.confidence})")
    print(f"[Classify] Indicators: {result.indicators}")

    return {"classification": result.classification}


def should_continue_after_classify(state: AgentState) -> str:
    """Determine next step after classification.

    Args:
        state: Current agent state.

    Returns:
        "diagnose" if error/warning, "end" if normal.
    """
    classification = state.get("classification", "normal")

    if classification in ("error", "warning"):
        return "diagnose"
    else:
        print("No further action needed for normal log message.")
        return "end"


@mlflow.trace(name="diagnose_problem", span_type=SpanType.LLM)
def diagnose_problem(state: AgentState) -> dict:
    """Diagnose the root cause of an error or warning.

    This node has access to MCP research tools (DeepWiki, Context7) which the
    LLM can use to look up documentation and code references. The LLM decides
    whether to use tools based on the complexity of the issue.

    Args:
        state: Current agent state with log_message and classification.

    Returns:
        Updated state with diagnosis field.
    """
    from .tools import get_mcp_tools, get_research_tool_guidance

    log_message = state["log_message"]
    classification = state["classification"]

    print("[Diagnose] Analyzing root cause...")

    llm = get_llm()

    # Get MCP tools and bind them to the LLM
    try:
        mcp_tools = get_mcp_tools()
        llm_with_tools = llm.bind_tools(mcp_tools)
        tool_guidance = get_research_tool_guidance()
        print("[Diagnose] MCP research tools available")
    except Exception as e:
        print(f"[Diagnose] Warning: Could not load MCP tools: {e}")
        print("[Diagnose] Proceeding without research tools")
        llm_with_tools = llm
        tool_guidance = ""

    prompt = f"""Analyze this {classification} log message and diagnose the root cause.

Log message: {log_message}
{tool_guidance}
Provide a brief diagnosis explaining:
1. What went wrong
2. Likely root cause
3. Potential impact

Keep the diagnosis concise (1-2 sentences)."""

    result = llm_with_tools.invoke(prompt)
    diagnosis = result.content

    print(f"[Diagnose] Diagnosis: {diagnosis}")

    return {"diagnosis": diagnosis}


@mlflow.trace(name="assess_severity", span_type=SpanType.LLM)
def assess_severity(state: AgentState) -> dict:
    """Assess the severity of a diagnosed problem.

    Determines whether the issue requires immediate attention (high severity,
    routes to Slack alert) or can be tracked via ticket (low severity,
    routes to GitHub issue).

    Args:
        state: Current agent state with diagnosis.

    Returns:
        Updated state with severity field.
    """
    diagnosis = state["diagnosis"]
    log_message = state["log_message"]

    llm = get_llm()
    structured_llm = llm.with_structured_output(SeverityAssessmentSchema)

    prompt = f"""Assess the severity of this problem.

Log message: {log_message}
Diagnosis: {diagnosis}

Determine if this is HIGH or LOW severity:
- HIGH: Immediate user impact, service degradation, data loss risk, security issue
- LOW: Can wait for normal business hours, minor inconvenience, cosmetic issue

If uncertain, default to LOW severity."""

    try:
        result = structured_llm.invoke(prompt)
        severity = result.severity
        print(f"[Severity] Assessment: {severity} (confidence: {result.confidence})")
        print(f"[Severity] Reasoning: {result.reasoning}")
    except Exception:
        # Default to low severity when uncertain (per spec edge case)
        severity = "low"
        print("[Severity] Unable to determine severity, defaulting to low")

    return {"severity": severity}


def route_by_severity(state: AgentState) -> str:
    """Route to appropriate action based on severity.

    Args:
        state: Current agent state.

    Returns:
        "alert_sre" for high severity, "manage_ticket" for low severity.
    """
    severity = state.get("severity", "low")

    if severity == "high":
        return "alert_sre"
    else:
        return "manage_ticket"


@mlflow.trace(name="alert_sre", span_type=SpanType.TOOL)
def alert_sre(state: AgentState) -> dict:
    """Send alert to SRE via Slack (stub implementation).

    This is a stub that prints a log message. In production, this would
    integrate with the Slack API.

    Args:
        state: Current agent state.

    Returns:
        Updated state with action_taken field.
    """
    from .tools import send_slack_alert

    diagnosis = state["diagnosis"]
    severity = state["severity"]

    send_slack_alert(
        message=f"High severity issue detected - {diagnosis}",
        severity=severity,
        diagnosis=diagnosis,
    )

    return {"action_taken": "slack_alert"}


@mlflow.trace(name="manage_github_ticket", span_type=SpanType.TOOL)
def manage_github_ticket(state: AgentState) -> dict:
    """Check for existing GitHub issue and create if needed (stub).

    This is a stub that prints log messages. In production, this would
    integrate with the GitHub API.

    Args:
        state: Current agent state.

    Returns:
        Updated state with action_taken field.
    """
    from .tools import check_existing_github_issue, create_github_issue

    log_message = state["log_message"]
    diagnosis = state["diagnosis"]

    # Check if issue already exists
    issue_exists = check_existing_github_issue(query=diagnosis)

    if not issue_exists:
        # Create new issue
        create_github_issue(
            title=f"[Auto] {log_message[:50]}...",
            body=f"## Log Message\n{log_message}\n\n## Diagnosis\n{diagnosis}",
        )

    return {"action_taken": "github_ticket"}


@mlflow.trace(name="set_no_action", span_type=SpanType.TOOL)
def set_no_action(state: AgentState) -> dict:
    """Set action_taken to none for normal logs.

    Args:
        state: Current agent state.

    Returns:
        Updated state with action_taken field.
    """
    return {"action_taken": "none"}


# =============================================================================
# Workflow Definition
# =============================================================================


def build_workflow() -> StateGraph:
    """Build the log monitor agent workflow.

    Returns:
        Compiled StateGraph ready for execution.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classify", classify_log)
    workflow.add_node("set_no_action", set_no_action)
    workflow.add_node("diagnose", diagnose_problem)
    workflow.add_node("assess_severity", assess_severity)
    workflow.add_node("alert_sre", alert_sre)
    workflow.add_node("manage_ticket", manage_github_ticket)

    # Set entry point
    workflow.set_entry_point("classify")

    # Add conditional edges after classification
    workflow.add_conditional_edges(
        "classify",
        should_continue_after_classify,
        {
            "diagnose": "diagnose",
            "end": "set_no_action",
        },
    )

    # Diagnose -> Assess Severity
    workflow.add_edge("diagnose", "assess_severity")

    # Add conditional edges after severity assessment
    workflow.add_conditional_edges(
        "assess_severity",
        route_by_severity,
        {
            "alert_sre": "alert_sre",
            "manage_ticket": "manage_ticket",
        },
    )

    # Terminal edges
    workflow.add_edge("set_no_action", END)
    workflow.add_edge("alert_sre", END)
    workflow.add_edge("manage_ticket", END)

    return workflow.compile()


# =============================================================================
# Public API
# =============================================================================

# Compiled workflow instance
_workflow = None


def get_workflow():
    """Get the compiled workflow instance (lazy initialization)."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
    return _workflow


@mlflow.trace(name="process_log_message", span_type=SpanType.AGENT)
def process_log_message(log_message: str) -> dict:
    """Process a single log message through the agent workflow.

    This is the main entry point for the agent. It accepts a plain text
    log message and runs it through the classification -> diagnosis ->
    severity -> action workflow.

    Args:
        log_message: Raw log text from a deployed server.

    Returns:
        Final state dict with classification, diagnosis, severity, action_taken.

    Example:
        >>> process_log_message("ERROR: Database connection failed")
        [Classify] Classification: error (confidence: 0.95)
        ...
    """
    with mlflow.start_span(name="initialize_state", span_type=SpanType.TOOL) as span:
        span.set_inputs({"log_message": log_message[:200]})
        initial_state: AgentState = {
            "log_message": log_message,
            "classification": "",
            "diagnosis": "",
            "severity": "",
            "action_taken": "",
        }
        span.set_outputs({"state_keys": list(initial_state.keys())})

    with mlflow.start_span(name="workflow_execution", span_type=SpanType.CHAIN) as span:
        span.set_inputs({"log_message_preview": log_message[:100]})
        workflow = get_workflow()
        final_state = workflow.invoke(initial_state)
        span.set_outputs({
            "classification": final_state.get("classification"),
            "severity": final_state.get("severity"),
            "action_taken": final_state.get("action_taken"),
        })

    print(f"Action taken: {final_state.get('action_taken', 'none')}")
    return final_state
