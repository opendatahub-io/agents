This is a simple example of making an MCP tool call against the Google
Workspace MCP server from
https://github.com/taylorwilsdon/google_workspace_mcp.

Getting an appropriate bearer token for use with this MCP server is
not trivial. The provided example implements a rudimentary flow to
automatically obtain one under the account of the user running the
example, once they have authenticated and granted permission. For this
the following two environment variables need to be set to the details
as configured in the Google Workspace project:

* GOOGLE_OAUTH_CLIENT_ID
* GOOGLE_OAUTH_CLIENT_SECRET

Follow the instructions from the MCP servers README at
https://github.com/taylorwilsdon/google_workspace_mcp?tab=readme-ov-file#configuration
to setup a client.

To run the example there are some other environment variables
that need to be set:

* OPENAI_BASE_URL should be set to point at the responses API
  server. In the case of a local LlamaStack instance that would be
  e.g. <http://localhost:8321/v1/openai/v1>

* OPENAI_API_KEY should be set to your OpenAI API key if using an
  OpenAI provided model (which it does by default)

* INFERENCE_MODEL can be used to alter the model used

To run Go script:

```
go mod tidy
go run google-doc-mcp-example.go
```

or Python (from within the project root venv):
```
python google-doc-mcp-example.py
```

## Running the MCP server for this example

To run the MCP server in a configuration that supports this example,
the following environment variables need to be set:

```
OAUTHLIB_INSECURE_TRANSPORT=1
USER_GOOGLE_EMAIL=<whatever email associated with the google client created>
WORKSPACE_MCP_BASE_URI=http://localhost
WORKSPACE_MCP_PORT=9876
MCP_ENABLE_OAUTH21=true
GOOGLE_OAUTH_CLIENT_ID=<client id as downloaded from google workspace console>
GOOGLE_OAUTH_CLIENT_SECRET=<client secret as downloaded from google workspace console>
```

Then, after cloning the MCP server repo, in the base directory run:

```
uv run main.py --tools docs --transport streamable-http
```


