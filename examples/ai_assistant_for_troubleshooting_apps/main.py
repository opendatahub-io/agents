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

    # OpenAI API key to use gpt-4 model
    - OPENAI_API_KEY
"""

import os
from datetime import datetime

from crew import TroubleshootingCrew

if __name__ == "__main__":
    inputs = {
        'repo': os.getenv("REPO_NAME", "demo-cluster-resources"),
        'owner': os.getenv("OWNER", "s-akhtar-baig"),
        'branch': f'update_spec_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}',
        'channel': "#social",
    }

    try:
        result = TroubleshootingCrew().crew().kickoff(inputs=inputs)

        print("Testing Troubleshooting crew:")
        print(result)

    except Exception as e:
        raise Exception(f"An error occurred while testing the troubleshooting crew: {e}")
