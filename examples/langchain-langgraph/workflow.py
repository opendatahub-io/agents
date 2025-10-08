import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Literal
from openai import OpenAI
import os
import json

# Configure logging
logger = logging.getLogger(__name__)


class State(TypedDict):
    input: str
    classification_message: str
    messages: Annotated[list, add_messages]
    decision: str
    namespace: str
    data: str
    mcp_output: str
    github_issue: str
    submissionID: str

# Global dictionary to store state by submission ID
submission_states: dict[str, State] = {}


class ClassificationSchema(BaseModel):
    """Analyze the message and route it according to its content."""

    classification: Literal["legal", "support", "unsafe", "unknown"] = Field(
        description="""The classification of the input: 'set to 'legal' if the input is a query related to legal, 'support' if related to software support, or
        'unsafe' if the input fails the moderation/safety check, and 'unknown' for everything else.
        Examples of legal questions that can be processed:
        - questions about various software licenses
        - embargoes for certain types of software that prevent delivery to various countries outside the United States
        - privacy, access restrictions, around customer data (sometimes referred to as PII)
        Examples of support, specifically software support, that can be processed
        - the user cites problems running certain applications of the company's OpenShift Cluster
        - the user asks to have new applications deployed on the company's OpenShift Cluster
        - the user needs permissions to access certain resources on the company's OpenShift Cluster
        - the user asks about current utilization of resources on the company's OpenShift Cluster
        - the user cites issues with performance of their application specifically or the OpenShift Cluster in general
        """,
    )


def classification_agent(state: State):

    safetyResponse = openaiClient.moderations.create(model=GUARDRAIL_MODEL, input=state["input"])
    for moderation in safetyResponse.results:
        if moderation.flagged:
            logger.info(f"Classification result: '{state['input']}' is flagged as '{moderation}'")
            state['decision'] = 'unsafe'
            state['data'] =  state['input']
            flagged_categories = [key for key, value in moderation.categories.model_extra.items() if value is True]
            state['classification_message'] =  f"Classification result: '{state['input']}' is flagged for: {', '.join(flagged_categories)}"
            submission_states[state['submissionID']] = state
            return state

    # Determine the topic of the message
    classification_llm = llm.with_structured_output(ClassificationSchema, include_raw=True)
    # this invoke will in fact POST to the llama stack OpenAI Responses API.
    response = classification_llm.invoke([{'role': 'user', 'content': 'Determine what category the user message falls under based on the classification schema provided to the structured output set for the LLM and the various classification agent nodes in the LangGraph StateGraph Agentic AI application : ' + state['input']}])
    classification_result = response['parsed']
    # the raw_response object has a 'response_metadata' dict field that has elements from the underlying OpenAI Response API object as populated by llama stack
    raw_response = response['raw']
    parsing_error = response.get('parsing_error')
    logger.info(f"Classification result: {classification_result} for input '{state['input']}'")
    if 'legal' == classification_result.classification:
        state['decision'] = 'legal'
        state['data'] = state['input']
    elif 'support' == classification_result.classification:
        state['decision'] = 'support'
        state['data'] = state['input']
    else:
        state['decision'] = 'unknown'
        state['data'] = state['input']
        state['classification_message'] = "Unable to determine request type."

    sub_id = state['submissionID']
    submission_states[sub_id] = state
    return state

def route_to_next_node(state: State) -> Literal['legal_agent', 'support_agent', '__end__']:
    if state['decision'] == 'legal':
        return 'legal_agent'
    elif state['decision'] == 'support':
        return 'support_agent'
    else:
        return '__end__'

class SupportClassificationSchema(BaseModel):
    """Analyze the message and route it according to its content."""

    classification: Literal["pod", "perf", "git"] = Field(
        description="""
        The classification of the input: set the classification to 'perf' if there is any mention of
        - performance
        - the application is slow to respond
        - questions around CPU or memory consumption or usage
        However, set the classification to 'pod' if the input asks for
        - assistance with an application, and
        - makes any reference to a 'Namespace' or 'Project' that exists within OpenShift or Kubernetes

        Otherwise, set the classification to 'git'.
        """,
    )
    namespace: str = Field(
        description="""
        the namespace of the input: if the query makes any reference to a namespace or project of a given name, then set the
        namespace field here to the first given name referenced as a namespace or project.
        """,
    )
    performance: str = Field(
        description="""
        if the query makes any reference to performance, applications running slowly, CPU or memory utilization or consumption, then
        set the performance field to 'true'.  Otherwise, if there is no mentioned of performance, being slow, CPU or memory,
        set the performance field to 'false' or an empty string.
        """,
    )

def support_classification_agent(state: State):

    support_classification_llm = llm.with_structured_output(SupportClassificationSchema, include_raw=True)
    response = support_classification_llm.invoke([
        {'role': 'user',
         'content': 'Determine what category the user message falls under based on the classification schema provided to the structured output set for the LLM and the various classification agent nodes in the LangGraph StateGraph Agentic AI application : ' + state['input']
         }])
    classification_result = response['parsed']
    parsing_error = response.get('parsing_error')
    logger.info(f"Support Classification result: {classification_result} for input '{state['input']}' and parsing error {parsing_error}")
    state['namespace'] = classification_result.namespace
    if 'perf' == classification_result.classification or classification_result.performance == 'true' or classification_result.performance == 'performance issue':
        state['decision'] = 'perf'
        state['data'] = state['input']
    elif 'pod' == classification_result.classification:
        state['decision'] = 'pod'
        state['data'] = state['input']
    else:
        state['decision'] = 'git'
        state['data'] = state['input']

    sub_id = state['submissionID']
    saved_state = submission_states.get(sub_id, {})
    state['classification_message'] = saved_state.get('classification_message', state.get('classification_message', ''))
    submission_states[sub_id] = state
    return state

def support_route_to_next_node(state: State) -> Literal['pod_agent', 'perf_agent', 'git_agent', '__end__']:
    if state['decision'] == 'pod':
        return 'pod_agent'
    elif state['decision'] == 'git':
        return 'git_agent'
    elif state['decision'] == 'perf':
        return 'perf_agent'

    return '__end__'

def git_agent(state: State):
    subId = state['submissionID']
    logger.info(f"git Agent request for submission: {state['submissionID']}")

    openai_mcp_tool = {
        "type": "mcp",
        "server_label": "github",
        "server_url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            "Authorization": f"Bearer {GIT_TOKEN}"
        },
        "allowed_tools": ["create_issue"]
    }
    # get state updated by other agents
    user_question = state['input']
    initial_classification = state.get('mcp_output', '')
    try:
        logger.info("git_agent GIT calling response api")
        resp = openaiClient.responses.create(
            model=MCP_TOOL_MODEL,
            input=f"""
                Using the supplied github tool, call the 'create_issue' tool to create an issue against the {GITHUB_URL} repository. For the title of the issue, use the string 'test issue {subId}'.
                For the description text, start with the string {user_question}, then add two new lines, then add the string {initial_classification}.  For the 'assignee' parameter, use the string {GITHUB_ID}.
                For the 'labels' parameter, supply a label that is string 'bug'.  This is the only label we need to provide.  For the 'milestone' parameter, use the integer '1'.  For the parameter that captures the type of the issue, supply the string value of 'Bug'.
                """,
            tools=[openai_mcp_tool]
        )
        logger.info("git_agent response returned")
        mcp_output = None
        # can we assume that the 'McpCall' entry in resp.output is always at index 1 ? ... seem fragile, but by
        # comparison this check
        for item in resp.output:
            if hasattr(item, '__class__') and item.__class__.__name__ == 'McpCall':
                # Parse the JSON output and extract the URL field
                output_json = json.loads(item.output)
                mcp_output = output_json.get('url', item.output)
                print(mcp_output)
                break
        state['github_issue'] = mcp_output
        submission_states[subId] = state
    except Exception as e:
        logger.info(f"git_agent Tool failed with error: '{e}'")
    return state

def pod_agent(state: State):
    subId = state['submissionID']
    logger.info(f"K8S Agent request for submission: {state['submissionID']}")

    # using open ai response client vis-a-vis testOpenAIMCP
    openai_mcp_tool = {
        "type": "mcp",
        "server_label": "OpenShift / Kubernetes MCP Tools",
        "server_url": "http://localhost:8080/mcp",
        "require_approval": "never",
        "allowed_tools": ["pods_list_in_namespace"]
    }
    ns = state['namespace']
    try:
        logger.info(f"K8S Agent making MCP request for submission: {state['submissionID']}")
        resp = openaiClient.responses.create(
            model=MCP_TOOL_MODEL,
            input=f"Using the supplied kubernetes tool, list all the pods in the '{ns}' namespace.  Only use the namespace as a parameter and don't bother further filtering on labels.   The `labelSelector` parameter is in fact NOT required.",
            tools=[openai_mcp_tool]
        )
        logger.info(f"K8S Agent successful return MCP request for submission: {state['submissionID']}")
        mcp_output = None
        # can we assume that the 'McpCall' entry in resp.output is always at index 1 ? ... seem fragile, but by
        # comparison this check
        for item in resp.output:
            if hasattr(item, '__class__') and item.__class__.__name__ == 'McpCall':
                mcp_output = item.output
                print(item.output)
                break
        state['mcp_output'] = mcp_output
        submission_states[subId] = state
    except Exception as e:
        logger.info(f"K8s Agent unsuccessful return MCP request for submission {state['submissionID']} with error: '{e}'")
    return state


def perf_agent(state: State):
    subId = state['submissionID']
    logger.info(f"K8S perf Agent request for submission: {state['submissionID']}")

    # using open ai response client vis-a-vis testOpenAIMCP
    openai_mcp_tool = {
        "type": "mcp",
        "server_label": "OpenShift / Kubernetes MCP Tools",
        "server_url": "http://localhost:8080/mcp",
        "require_approval": "never",
        "allowed_tools": ["pods_top"]
    }
    ns = state['namespace'] # "openshift-console"
    try:
        logger.info(f"K8S perf Agent making MCP request for submission: {state['submissionID']}")
        resp = openaiClient.responses.create(
            model=MCP_TOOL_MODEL,
            input=f"Using the supplied kubernetes tool, get pod memory and cpu resource consumption in the '{ns}' namespace.  Only use the namespace as a parameter and don't bother further filtering on labels.   The `labelSelector` parameter is in fact NOT required.  If namespace is not set, then call the 'pods_top' tool without any parameters",
            tools=[openai_mcp_tool]
        )
        logger.info(f"K8S perf Agent successful return MCP request for submission: {state['submissionID']}")
        mcp_output = None
        # can we assume that the 'McpCall' entry in resp.output is always at index 1 ? ... seem fragile, but by
        # comparison this check
        for item in resp.output:
            if hasattr(item, '__class__') and item.__class__.__name__ == 'McpCall':
                mcp_output = item.output
                print(item.output)
                break
        state['mcp_output'] = mcp_output
        submission_states[subId] = state
    except Exception as e:
        logger.info(
            f"K8s perf Agent unsuccessful return MCP request for submission {state['submissionID']} with error: '{e}'")
    return state

from typing import Optional, Mapping, Any
def create_department_agent(
        department_name: str,
        department_display_name: str,
        content_override: Optional[str] = None,
        custom_llm = None,
        submission_states: Mapping[str, "State"] | dict | None = None):
    """Factory function to create department-specific agents with consistent structure."""

    # Use custom_llm if provided, otherwise default to topic_llm
    if custom_llm is None:
        raise ValueError("custom_llm is required")
    llm_to_use = custom_llm
    if submission_states is None:
        raise ValueError("submission_states is required")

    def llm_node(state: State):
        logger.info(f"{department_display_name} LLM node '{state}'")
        message = llm_to_use.invoke(state["messages"])
        state["messages"] = message
        sub_id = state["submissionID"]
        cm = getattr(message, "content", getattr(message, "text", str(message)))
        state['classification_message'] = cm
        submission_states[sub_id] = state
        return state

    def init_message(state: State):
        logger.info(f"init {department_name} message '{state}'")
        if content_override:
            content = content_override
        else:
            content = (
                    f"Summarize that the user query is classified as {department_display_name.lower()}, "
                    f"along with any answers provided by the LLM for the question, and include that we are responding "
                    f'to submissionID {state["submissionID"]}. Finally, mention a GitHub issue will be opened for follow up.'
            )
        return {"messages": [{'role': 'user', 'content': content}]}

    agent_builder = StateGraph(State)
    agent_builder.add_node(f"{department_name}_set_message", init_message)
    agent_builder.add_node("llm_node", llm_node)
    agent_builder.add_edge(START, f"{department_name}_set_message")
    agent_builder.add_edge(f"{department_name}_set_message", "llm_node")
    agent_workflow = agent_builder.compile()
    logger.info(agent_workflow.get_graph().draw_ascii())
    return agent_workflow


def make_workflow(topic_llm, openai_client, guardrail_model, mcp_tool_model, git_token, github_url, github_id):
    """Create and configure the overall workflow with all agents and routing."""

    # Set global variables needed by the agents
    global llm, openaiClient, GUARDRAIL_MODEL, MCP_TOOL_MODEL, GIT_TOKEN, GITHUB_URL, GITHUB_ID
    llm = topic_llm
    openaiClient = openai_client
    GUARDRAIL_MODEL = guardrail_model
    MCP_TOOL_MODEL = mcp_tool_model
    GIT_TOKEN = git_token
    GITHUB_URL = github_url
    GITHUB_ID = github_id

    # Create all department agents using the factory function
    legal_agent = create_department_agent("legal", "Legal", custom_llm=topic_llm, submission_states=submission_states)
    support_agent = create_department_agent("support", "Software Support", custom_llm=topic_llm, submission_states=submission_states)

    # Create the overall workflow
    overall_workflow = StateGraph(State)
    overall_workflow.add_node("classification_agent", classification_agent)
    overall_workflow.add_node("legal_agent", legal_agent)
    overall_workflow.add_node("support_agent", support_agent)
    overall_workflow.add_node("pod_agent", pod_agent)
    overall_workflow.add_node("perf_agent", perf_agent)
    overall_workflow.add_node("git_agent", git_agent)
    overall_workflow.add_node("support_classification_agent", support_classification_agent)
    overall_workflow.add_edge(START, "classification_agent")
    overall_workflow.add_conditional_edges("classification_agent", route_to_next_node)
    overall_workflow.add_edge("support_agent", "support_classification_agent")
    overall_workflow.add_conditional_edges("support_classification_agent", support_route_to_next_node)
    overall_workflow.add_edge("pod_agent", "git_agent")
    overall_workflow.add_edge("perf_agent", "git_agent")
    workflow = overall_workflow.compile()

    logger.info(workflow.get_graph().draw_ascii())

    return workflow