# Slack MCP Example

This example walks through creating and running a Slack MCP server, then connecting it to an LLM using responses API and OAuth tokens. Since OAuth
tokens offer high levels of granularity, do not expire, and can be rotated automatically in Slack, this method is more reliable and easier to manage for production users. However, Slack does also allow for stealth authentication using a combination of a browser and cookie token as well.

*NOTE* that this example is configured to work with a locally hosted llama stack instance and has been tested using QWEN running in a local instance of vLLM. Adjustments may need to be made based on your use case. To set things up to meet those conditions, please see the [llama-stack/local setup tools](../../tools/llama-stack/local/README.md), and the [vllm setup tools](../../tools/vllm/README.md).

## Create a Slack Application and OAuth Token

1. Go to the [slack applications page](https://api.slack.com/apps) and create a new app from scratch.
2. Navigate to "OAuth & Permissions" in your app's sidebar.
3. Under "Bot Token Scopes", configure the OAuth scope you want your bot to have access to. Be careful to avoid giving access to sensitive data or admin privelages if you can avoid it.
4. Click "Install to Workspace" to install the application if its available, otherwise contact an administrator and click "Request to Install".
5. Save the "Bot User OAuth Token" to a secure location 

NOTE: There are a set of minimum OAuth scopes needed for this MCP server to work. If the Bot Token Scopes do not include these scopes, the MCP server will not be able to serve requests.
- `channels:read`
- `groups:read`
- `mpim:read`
- `im:read`
- `users:read`

You can use the [slack/test-oauth.sh](slack/test-oauth.sh) script to verify that your token has the minimum required scopes.
```sh
./slack/test-oauth.sh
```

## Create your Slack MCP Server

For this example, we use a container image based on [slack-mcp-server](https://github.com/korotovsky/slack-mcp-server/tree/master): ghcr.io/korotovsky/slack-mcp-server:latest.

The [slack/run-mcp.sh](./slack/run-mcp.sh) script should handle this automatically for basic use cases. For more details on how to configure the slack-mcp-server container, read the [docs](https://github.com/korotovsky/slack-mcp-server/blob/master/docs/03-configuration-and-usage.md#Using-Docker).

*NOTE* This server binds ports to 127.0.0.1 by default in the container, which is inaccessible from outside of port forwards. Please override this by setting this env variable:

```sh
SLACK_MCP_HOST=0.0.0.0
```

If you use the `run-mcp.sh` script, it will handle this for you.

## Query the MCP Server

To run the client side example, you just need to run the Go script `client.go` once the MCP server is running.

If you are using llama stack, you can export the url its hosted at with environment variables so the go client code queries it:

```sh
export OPENAI_CLIENT_URL="http://127.0.0.1:8321/v1/openai/v1/"
```

1. Run Go mod tidy
```sh
go mod tidy
```
2. Run the demo script
```sh
go run client.go
```

Alternatively, to run the python example (from within the venv located at the repository root directory):

```
python client.py
```


### Expected Output

```
Here is the list of channels in the `channels_list` list response:

1. **C09E6KY97KJ**
   - ID: #all-mcp-testing
     - Topic: Share announcements and updates about company news, upcoming events, or teammates who deserve some kudos. ⭐
     - Purpose: Share announcements and updates about company news, upcoming events, or teammates who deserve some kudos.
     - MemberCount: 2
     - Cursor: C09E6KY97KJ

2. **D09DDLU5QJE**
   - ID: @slackbot
     - Topic: DM with Slackbot
     - Purpose: DM with Slackbot
     - MemberCount: 2
     - Cursor: D09DDLU5QJE
```
