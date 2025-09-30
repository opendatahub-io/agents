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

    # GitHub token
    gh_pat = os.getenv("GITHUB_TOKEN", None)
    
    # Configure GitHub MCP server
    mcp_server_params: Union[list[MCPServerAdapter | dict[str, str]], MCPServerAdapter, dict[str, str]] = {
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "streamable-http",
        "headers": {
            "Authorization": "Bearer " + gh_pat,
        }
    }

    @agent
    def developer(self) -> Agent:
        llm = LLM(
            model="openai/gpt-4",
        )

        return Agent(
            config=self.agents_config['developer'],
            verbose=True,
            tools=self.get_mcp_tools("create_branch", "create_or_update_file", "push_files", "create_pull_request"),
            llm=llm
        )

    # @task
    # def list_issues_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['list_issues_task']
    #     )

    @task
    def create_branch_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_branch_task']
        )

    @task
    def update_file_task(self) -> Task:
        return Task(
            config=self.tasks_config['update_file_task']
        )

    @task
    def create_pull_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_pull_request_task']
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

    
