This is a simple example of an MCP tool call to the GitHub remote MCP
server. To run the example there are several environment variables
that need to be set:

* GITHUB_TOKEN should be set to a personal access token (only requires read access)

* OPENAI_BASE_URL should be set to point at the responses API
  server. In the case of a local LlamaStack instance that would be
  e.g. <http://localhost:8321/v1/openai/v1>

* OPENAI_API_KEY should be set to your OpenAI API key if using an
  OpenAI provided model (which it does by default)

Run with: `go run github-mcp-example.go`.

or for Python (from within the venv at the repository root): `python github-mcp-example.py` 
