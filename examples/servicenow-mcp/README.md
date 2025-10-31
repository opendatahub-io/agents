This is a simple example of making an MCP tool call against the
servicenow MCP server from
https://github.com/echelon-ai-labs/servicenow-mcp in SSE mode. Note
that this server does not support authorisation. It uses credentials
set in its environment (as described in installation guide at that
link) to access the servicenow instance.

To run the example there are several environment variables
that need to be set:

* OPENAI_BASE_URL should be set to point at the responses API
  server. In the case of a local LlamaStack instance that would be
  e.g. <http://localhost:8321/v1/openai/v1>

* OPENAI_API_KEY should be set to your OpenAI API key if using an
  OpenAI provided model (which it does by default)

* INFERENCE_MODEL (optional) can override the default model used by
  the example program.

To run:

```
go mod tidy
go run servicenow-mcp-example.go
```

or for Python (from within the venv located at the repository root):
```
python servicenow-mcp-example.py
```

## Running the MCP server

First you need to set up the following environment variables:

```
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
SERVICENOW_AUTH_TYPE=basic
```

You can sign up with the servicenow developer program and request a
test instance to work with here: https://developer.servicenow.com/

Then, after cloning the mcp server repo, from the base directory run:

```
python -m venv .venv
source .venv/bin/activate
pip install -e .
servicenow-mcp-sse --host=127.0.0.1 --port=8000
```
