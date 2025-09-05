# MCP Server Tester

A Python tool for testing Model Context Protocol (MCP) servers using the Anthropic MCP client library. This is largely AI generated, so use it for surface level troubleshooting, and leave it at that.

Why would I use this?

Llama Stack and OpenAI use the Anthropic MCP library to make calls to MCP tools in their backends. If an error occurs, they often return filtered and unhelpful errors to the client, making it hard to troubleshoot. This simulates the tool‑calling behavior of the Responses API in both services, allowing you to get detailed error messages and troubleshoot more narrowly.

## Features

- ✅ Test MCP server connectivity via SSE (Server-Sent Events)
- ✅ Validate MCP protocol initialization
- ✅ List available tools from MCP servers
- ✅ Test tool execution with sample calls
- ✅ Comprehensive error reporting and diagnostics

## Requirements

- Python 3.12+
- UV package manager

## Installation

1. **Clone/navigate to this directory**
   ```bash
   cd tools/mcp-tester
   ```

2. **Create Python 3.12 virtual environment**
   ```bash
   uv venv --python 3.12 --seed
   source .venv/bin/activate
   ```

3. **Install dependencies with UV**
   ```bash
   uv sync
   ```

## Usage

### Method 1: Environment Variables (Recommended)
```bash
export MCP_TOKEN="your_mcp_server_token"
export MCP_SERVER_URL="http://localhost:8080/mcp"
python test-mcp-server.py
```

### Method 2: Interactive Prompts
```bash
python test-mcp-server.py
# Will prompt for:
# - MCP server token
# - MCP server URL
```

## What it Tests

1. **Connection** - Establishes SSE connection to MCP server
2. **Protocol** - Initializes MCP protocol handshake
3. **Tools Discovery** - Lists all available tools from server
4. **Tool Execution** - Calls the first available tool with empty arguments
5. **Error Handling** - Reports detailed error information for debugging

## Troubleshooting

- **Import errors**: Make sure `mcp` package is installed with `uv pip install mcp`
- **Connection refused**: Verify MCP server is running on specified URL
- **SSE connection issues**: Check if server supports SSE transport
- **401 Unauthorized**: Verify your MCP token is valid and has proper permissions

## Common MCP Server URLs

- **Local SSE**: `http://localhost:8080/sse`
- **Local HTTP**: `http://localhost:8080/mcp`
