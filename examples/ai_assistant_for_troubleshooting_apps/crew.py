import os

from crewai import LLM, Agent, Task, Crew
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import MCPServerAdapter

from typing import List, Union

@CrewBase
class TroubleshootingCrew():
    """
    A multi-system agent that can monitor a Kubernetes cluster and help troubleshoot problems.

    The crew comprises of three agents:
    1. Platform agent: monitors a cluster and provides remediation steps
    2. Notifier agent: sends updates via Slack
    3. Developer agent: creates changes in resource definitions, as needed, and pushes to GitHub

    The crew will execute in a sequential manner in the first iteration -- subsequent iterations will
    introduce a hierarchical process.

    Finally, the agent and task definitions are stored under the config folder.
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Kubernetes token
    kube_token = os.getenv("KUBE_TOKEN", None)

    # GitHub token
    gh_pat = os.getenv("GITHUB_TOKEN", None)

    # Configure multiple MCP servers
    mcp_server_params: Union[list[MCPServerAdapter | dict[str, str]], MCPServerAdapter, dict[str, str]] = [
        {
            "url": "http://localhost:8080/sse",
            "transport": "sse",
            # "headers": {
            #     "Authorization": "Bearer " + kube_token,
            # },
        },
        {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable-http",
            "headers": {
                "Authorization": "Bearer " + gh_pat,
            },
        },
        {
            "url": "http://localhost:13080/sse",
            "transport": "sse",
        },
    ]

    @agent
    def platform(self) -> Agent:
        llm = LLM(
            model="openai/gpt-4o",
        )

        return Agent(
            config=self.agents_config['platform'],
            verbose=True,
            tools=self.get_mcp_tools(),
            llm=llm
        )

    @agent
    def developer(self) -> Agent:
        llm = LLM(
            model="openai/gpt-4o",
        )

        return Agent(
            config=self.agents_config['developer'],
            verbose=True,
            tools=self.get_mcp_tools("create_branch", "get_file_contents", "create_or_update_file", "create_pull_request"),
            llm=llm
        )

    @agent
    def notifier(self) -> Agent:
        llm = LLM(
            model="openai/gpt-4o",
        )

        return Agent(
            config=self.agents_config['notifier'],
            verbose=True,
            tools=self.get_mcp_tools(),
            llm=llm
        )

    @task
    def diagnose_deployment_task(self) -> Task:
        return Task(
            config=self.tasks_config['diagnose_deployment_task']
        )

    @task
    def create_pull_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_pull_request_task'],
            context=[self.diagnose_deployment_task()],
        )

    @task
    def send_message_task(self) -> Task:
        return Task(
            config=self.tasks_config['send_message_task'],
            context=[self.create_pull_request_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

