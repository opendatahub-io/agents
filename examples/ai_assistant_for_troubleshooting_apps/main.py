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

import os
import sys
from datetime import datetime
from collections import deque

from crew import TroubleshootingCrew
from utils.k8s import KubernetesProbe


def get_issue_id(issue):
    return f"{issue['namespace']}-{issue['pod']}-{issue['reason']}"


if __name__ == "__main__":
    sys.tracebacklimit = 0
    inputs = {
        'repo': os.getenv("REPO_NAME", "demo-cluster-resources"),
        'owner': os.getenv("OWNER", "s-akhtar-baig"),
        'branch': f'update_spec_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}',
        'channel': "#social",
        'pod': "pod-reader-test",
        'namespace': "demo-auth",
    }

    seen_issues = set()
    print("Watching for issues in the K8s cluster...")

    while True:
        try:
            issues = KubernetesProbe().scan_namespaces()
            new_issues = []
            for issue in issues:
                if get_issue_id(issue) not in seen_issues:
                    new_issues.append(issue)

            if new_issues:
                print(f"Found the following issues in the K8s cluster:")
                print(new_issues)

        except Exception as e:
            raise Exception(f"An error occurred while scanning cluster for issues: {e}")

        for issue in issues:
            issue_id = get_issue_id(issue)
            if issue_id in seen_issues:
                continue

            seen_issues.add(issue_id)

            print(f"Diagnosing issue: {issue}")
            try:
                result = TroubleshootingCrew().crew().kickoff(inputs=inputs)

                print("Testing Troubleshooting crew:")
                print(result)

            except Exception as e:
                raise Exception(f"An error occurred while testing the troubleshooting crew: {e}")
