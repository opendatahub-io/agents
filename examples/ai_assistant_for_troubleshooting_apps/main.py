import os

from crew import TroubleshootingCrew

if __name__ == "__main__":
    inputs = {
        'repo': os.getenv("REPO_NAME", "demo-cluster-resources"),
        'owner': os.getenv("OWNER", "s-akhtar-baig")
    }

    try:
        result = TroubleshootingCrew().crew().kickoff(inputs=inputs)

        print("Testing Troubleshooting crew:")
        print(result)

    except Exception as e:
        raise Exception(f"An error occurred while testing the troubleshooting crew: {e}")
