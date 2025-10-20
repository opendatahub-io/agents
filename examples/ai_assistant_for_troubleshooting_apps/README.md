# AI Assistant for Troubleshooting Applications

A multi-agent system that can monitor a Kubernetes cluster and help troubleshoot problems.

The system will comprise of three agents:

- **Platform agent**: Monitors a cluster and provides remediation steps
- **Notifier agent**: Sends updates via Slack
- **Developer agent**: Creates changes in resource definitions, as needed, and pushes to GitHub

## Installation and Configuration

### Virtual Environment

Install [uv](https://docs.astral.sh/uv) to setup your virtual environment as shown below.

```
uv sync
source .venv/bin/activate
```

### GitHub Setup

#### 1. Create a GitHub Repository

If you don't already have a repository with your Kubernetes manifests, create a new one, and optionally use our sample manifest files:

1. Go to [GitHub](https://github.com) and sign in
2. Refer to the [official docs](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) for detailed instructions on creating a new repository
3. (Optional) Copy the provided sample manifest files to your repository. Sample manifest files are stored under the `sample_manifest_files` folder

#### 2. Generate a Fine-Grained Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → [Fine-grained tokens](https://github.com/settings/personal-access-tokens)
2. To get a detailed description of the required fields and steps, visit [Manage PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
3. Under Repository access, select the repository you want the token to access
4. Under Permissions, select
   - `Contents` (Access: Read and write)
   - `Pull requests` (Access: Read and write)
5. Click "Generate token"
6. **Copy the token** and set it as an environment variable: `export GITHUB_TOKEN=<your_gh_token>`

#### 3. Setup GitHub MCP Server

This use-case utilizes the remote MCP server hosted by GitHub. Users must obtain a fine-grained token (as described in step 2) to grant required permissions to the agents.

### Required Environment Variables

Ensure that the target GitHub repository name, user information, and credentials are set.

```
export REPO_NAME=<repo_name>
export OWNER=<username>
export GITHUB_TOKEN=<your_gh_token>
```

Set the desired Slack channel that will be used to send updates.

```
export SLACK_CHANNEL=<your-slack-channel>
```

Finally, set tokens associated to your OpenAI account and Kubernetes service account.
```
export OPENAI_API_KEY=<your_openai_key>
export KUBE_TOKEN=<your_k8s_token>
```

## Run the Sample Code

The provided crew can be executed as following:

```
uv run python main.py
```
