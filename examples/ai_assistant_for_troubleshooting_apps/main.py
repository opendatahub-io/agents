"""
A user can execute the troubleshooting crew locally. The crew monitors and updates
a Kubernetes cluster resources in a sequential manner.

Usage:
    uv run python main.py

Pre-requisites:
    # GitHub repo information and user credentials
    - REPO_NAME
    - OWNER
    - GITHUB_TOKEN
    - KUBE_TOKEN

    # OpenAI API key to use gpt-4 model
    - OPENAI_API_KEY
"""

import asyncio
import sys

from orchestrator import Orchestrator

async def main():
    try:
        orchestrator = Orchestrator()
        await orchestrator.monitor_cluster()
    except Exception as exp:
        raise Exception(f"An error occurred while monitoring the k8s cluster: {exp}")


if __name__ == "__main__":
    sys.tracebacklimit = 0

    asyncio.run(main())
