import os

from crewai import LLM, Agent, Task, Crew
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import MCPServerAdapter

from typing import List, Union

@CrewBase
class TroubleshootingCrew():
    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # GitHub token
    gh_pat = os.getenv("GITHUB_TOKEN", None)
    
    # Configure GitHub MCP server
    mcp_server_params: Union[list[MCPServerAdapter | dict[str, str]], MCPServerAdapter, dict[str, str]] = {
        "url": "https://api.githubcopilot.com/mcp/x/issues",
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
            tools=self.get_mcp_tools(),
            llm=llm
        )

    @task
    def list_issues_task(self) -> Task:
        return Task(
            config=self.tasks_config['list_issues_task']
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

    
