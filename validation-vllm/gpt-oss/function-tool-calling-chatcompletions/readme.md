# Validate Function Tool Calling with GPT-OSS via Chat Completions API (RHAIENG-2236)

## Objective

Manually test that GPT-OSS models can correctly invoke function tools through the Llama Stack Chat Completions API.

## Test Results (01/15/2026)

✅ Both **GPT-OSS-120b** and **GPT-OSS-20b** correctly invoke function tools via vLLM current main branch.

## Setup

1. **vLLM**: Started on EC2 instance with GPT-OSS models using vLLM latest branch
2. **Llama Stack**: Exported the vLLM URL (`export VLLM_URL=http://localhost:8000/v1`), port forwarded, then started Llama Stack server using `llama stack run starter`
3. **.env**: Set `LLAMA_STACK_URL=http://localhost:8321`
4. **Function Tool**: Created a weather function calling agent using the Chat Completions API with a `get_weather` tool that fetches real data

## Notebooks

| Notebook | Model | vLLM Version |
|----------|-------|--------------|
| [`GPT-OSS-20b with vLLM.ipynb`](./GPT-OSS-20b%20with%20vLLM.ipynb) | GPT-OSS-20b | main |
| [`GPT-OSS-120b with vLLM.ipynb`](./GPT-OSS-120b%20with%20vLLM.ipynb) | GPT-OSS-120b | main |

Each notebook tests a weather function tool that fetches real weather data.

## Analysis

**Both GPT-OSS-20b and GPT-OSS-120b successfully invoke function tools through Llama Stack Chat Completions API** using vLLM current main branch.