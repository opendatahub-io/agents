#! /bin/bash

echo "Running Slack MCP Server"
echo "--------------------------------"

if [ -z "$SLACK_MCP_TOKEN" ]; then
    echo "Enter your Slack MCP Token: "
    read -s SLACK_MCP_TOKEN
fi

podman pull ghcr.io/korotovsky/slack-mcp-server:latest

podman run -d \
    --name slack-mcp-server \
    --replace \
    -e SLACK_MCP_XOXP_TOKEN="${SLACK_MCP_TOKEN}" \
    -e SLACK_MCP_LOG_LEVEL=debug \
    -e SLACK_MCP_HOST=0.0.0.0 \
    -e SLACK_MCP_ADD_MESSAGE_TOOL=true \
    -p 13080:13080 \
    ghcr.io/korotovsky/slack-mcp-server:latest \
    mcp-server --transport sse

echo "Slack MCP Server running on port 13080 (SSE transport)"
