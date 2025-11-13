# GitHub/JIRA Reporting with OAuth Authentication

This repository gives an example of a reporting tool built on [Llama Stack](https://llamastack.github.io/) that integrates with [GitHub Remote MCP](https://github.com/github/github-mcp-server) and a locally running [JIRA MCP Server](https://github.com/sooperset/mcp-atlassian), with access control.

## Known Limitations

* Depending on the model being used, tool calling can be unreliable.
* Queries may have to be specific. For example, `what's new with my projects` might result in being asked to name a specific project to request status for.


## Usage

Install Llama Stack:

```sh
pip install -U llama_stack
```

Start the Llama Stack server with the provided configuration:
```sh
llama stack run run.yaml
```

### Access Control

Note the `auth` block at the end of `run.yaml`. Follow [the `jwks-simple` README](https://github.com/anastasds/jwks-simple/tree/llamastack) for setting up a simple JWKS server for development/testing to simulate OAuth authentication, or use an OAuth provider available to you.

With the server running, obtain and store a token:

```sh
TOKEN=$(curl -X POST localhost:3000/token | jq -r .token)
```

This example uses OpenAI. After defining `OPENAI_API_KEY`, verify that Llama Stack successfully calls OpenAI APIs:
```sh
curl --silent -X POST --header "Authorization: Bearer $TOKEN" localhost:8321/v1/openai/v1/responses -d '{
   "model": "gpt-4",
    "input": "Tell me a three sentence bedtime story about a unicorn."
}'
```

### MCP Integration

Use the provided `docker-compose.yaml` file to start a JIRA server after adding your GitHub and JIRA credentials as per those projects' respective documentation:

```sh
docker-compose up
```

or
```sh
podman compose --file docker-compose.yml up
```

Finally, run a test query with tool calling configured and with a GitHub access token (replace `github_token` below) and using the same `TOKEN` obtained above using `jwks-simple`:

```sh
curl -s -v http://localhost:8321/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "openai/gpt-4",
    "input": "show me the latest changes",
    "tools": [
      {
        "type": "mcp",
        "server_label": "jira",
        "server_description": "JIRA",
        "server_url": "http://localhost:8000/sse",
        "require_approval": "never"
      },
      {
        "type": "mcp",
        "server_label": "github",
        "server_description": "GitHub",
        "server_url": "https://api.githubcopilot.com/mcp/x/repos/readonly",
        "require_approval": "never",
        "headers": {"Authorization": "Bearer github_token"}
      }
    ]
  }'
```

Try changing the query and model to explore the abilities and limitations of what this formula is capable of. For example, you may have to specifically ask for the commits in a particular GitHub repository as this setup does not have multi-turn conversational handling, i.e., cannot issue one query to get a list of available projects and than another to get more detailed information to summarize for you.

#### Examples

This setup is a good example of the abilities and limitations of a single request/response model with an MCP-enabled model. For example, a specific query such as `whats new with with repository llamastack/llama-stack` succeeds, with a response that looks like

```text
The latest release for the repository `llamastack/llama-stack` is `v0.3.1` and it was published on 2025-10-31. The changes include:\n\n- Fixes for 0.3.1 release \n- Install client from release branch before uv sync\n- Handle missing external_providers_dir\n- Unset empty UV index
```

Meanwhile, a general query such as `whats new with my project` gets a response like:

```text
I'm sorry, but without any specific project information or context, it's not possible to generate an update. Could you please provide the name or detail of the project you want updates for?
```

In order to serve this query, the application would have to first query for a list of available projects, then query for information for each project, and then summarize. At the time of this writing, that is not something that is automatically done.

### Access Control Validation

Replace `permit` with `forbid` in the `run.yaml` and restart `llamastack` to see that user `alice@example.com` is no longer allowed access to e.g. the models endpoint:

```sh
curl -X POST --silent --header "Authorization: Bearer $TOKEN" --header "Content-Type: application/json" localhost:8321/v1/models -d '{"model_id": "gpt-4o", "provider_id": "openai", "provider_model_id": "gpt-4o", "provider_type": "remote::openai", "metadata": {}, "model_type": "llm"}'
```
