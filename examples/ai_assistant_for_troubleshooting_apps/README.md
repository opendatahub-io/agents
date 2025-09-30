# AI Assistant for Troubleshooting Applications

A multi-agent system that can monitor a Kubernetes cluster and help troubleshoot problems.

The system will comprise of three agents:

- **Platform agent**: Monitors a cluster and provides remediation steps
- **Notifier agent**: Sends updates via Slack
- **Developer agent**: Creates changes in resource definitions, as needed, and pushes to GitHub

## Installation and Configuration

Install [uv](https://docs.astral.sh/uv) to setup your virtual environment as shown below.

```
uv sync
source .venv/bin/activate
```

Export the target GitHub repository name, the associated owner's username, GitHub API token, and OpenAI API token before running the provided scripts.

```
export REPO_NAME=<repo_name>
export OWNER=<username>
export GITHUB_TOKEN=<your_gh_token>
export OPENAI_API_KEY=<your_openai_key>
```

## Run the Sample Code

The provided crew can be executed as following:

```
uv run python main.py
```