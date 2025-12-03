# Agentic Examples

Within this directory are several examples highlighting the usage of Llama Stack's Responses API implementation.

## Example setup for MCP workflows

The MCP examples contained in the subdirectories of this folder are configurable to run across a variety of envirenments. Outlined below are instructions for setting up one such configuration, which assumes a local Llama Stack instance and MCP server, and a remote vLLM inference server hosting your chosen model. Instructions for setting up individual MCP servers are documented in their respective subdirectories.

### vLLM

> Note: if using an OpenAI provided model, you can forego the need for vLLM. Skip to the Llama Stack section to see guidance for configuring Llama Stack with your chosen OpenAI model.

This setup assumes a vLLM inference server reachable at port 8000. If hosting vLLM remotely such as on an EC2, you can port-forward requests with:

```
ssh  -N -f -L 8000:127.0.0.1:8000 <remote-server-url>
```

When launching vLLM, you will need to set the `enable-auto-tool-choice` flag and select a tool call parser.

```
python -m vllm.entrypoints.openai.api_server --model <model_name> --enable-auto-tool-choice --tool-call-parser hermes
```

### Llama Stack

Ensure that Llama Stack is correctly installed and configured locally. In this directory you will find an example `run.yaml` that you can use to base your instance off of. By default, it assumes you are serving `Qwen/Qwen3-1.7B` over vLLM as previously outlined, so you should modify the value of `model_id` if using a different model.

To launch Llama Stack with this configuration, open a separate terminal pane and run:

```
llama stack run run.yaml --image-type venv
```

> Note: if you with to use an OpenAI provided model, uncomment the relevant openai configuration fields in your `run.yaml`. Also, ensure before running the above command that the `OPENAI_API_KEY` environment variable is set to your OpenAI API key, and `INFERENCE_MODEL` is set to your chosen model using the `openai/<model_name>` naming convention. If unset, `INFERENCE_MODEL` will default to `openai/gpt-4o`

### Responses API

In this example environment, we are using Llama Stack as our responses API server. As such you will need to set the environment variable `OPENAI_BASE_URL=http://localhost:8321/v1/openai/v1` in the same terminal process where you run your python or go scripts.
