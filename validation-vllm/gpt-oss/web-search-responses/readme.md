# Validate Web Search Tool Calling with GPT-OSS via Responses API (RHAIENG-2241)

## Objective

Manually test that GPT-OSS models can correctly trigger and use web search results through the Llama Stack Responses API.

## Test Results (2026-01-19)

⚠️ **GPT-OSS-20b** with **vLLM 0.11.2+rhai5**: prompt 1 returned `status=completed` with empty output text; prompt 2 returned `status=incomplete`; prompt 3 completed.

⚠️ **GPT-OSS-120b** with **vLLM 0.11.2+rhai5**: prompt 2 returned `status=incomplete` with empty output text; prompts 1 and 3 completed.

## Setup

1. **vLLM**: Start GPT-OSS models on the target vLLM versions (e.g., `main` and `0.11.2+rhai5`)
2. **Llama Stack**: Ensure the Responses API is exposed (example: `http://127.0.0.1:8321`)
3. **Web Search**: Configure the Tavily integration in the Llama Stack server environment (e.g., `TAVILY_API_KEY`)
4. **.env**: Set `LLAMA_STACK_URL=http://127.0.0.1:8321` (or rely on notebook defaults)

## Test Matrix

| Model | vLLM Version |
|------|---------------|
| GPT-OSS-20b | 0.11.2+rhai5 |
| GPT-OSS-120b | 0.11.2+rhai5 |

## Notebooks

| Notebook | Model | vLLM Version |
|----------|-------|--------------|
| [`GPT-OSS-20b with vLLM 0.11.2+rhai5.ipynb`](./GPT-OSS-20b%20with%20vLLM%200.11.2%2Brhai5.ipynb) | GPT-OSS-20b | 0.11.2+rhai5 |
| [`GPT-OSS-120b with vLLM 0.11.2+rhai5.ipynb`](./GPT-OSS-120b%20with%20vLLM%200.11.2%2Brhai5.ipynb) | GPT-OSS-120b | 0.11.2+rhai5 |

## Test Scenarios (Prompts)

Use prompts that require recent information so the model must invoke web search:

1. "What were the top 3 headlines about NVIDIA in the last 7 days? Include sources."
2. "What is the latest stable release of vLLM and its release date? Cite sources."
3. "What is the most recent U.S. CPI (inflation) release and its month-over-month value? Cite sources."

## Python Snippet (Responses API + Web Search)

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8321/v1", api_key="none")
response = client.responses.create(
    model="vllm/openai/gpt-oss-20b",
    tools=[{"type": "web_search"}],
    input="What were the top 3 headlines about NVIDIA in the last 7 days? Include sources."
)
print(response.output_text)
```

## Results Summary

| Model | vLLM Version | Web Search Triggered | Result Quality | Notes |
|------|---------------|----------------------|----------------|-------|
| GPT-OSS-20b | 0.11.2+rhai5 | ✅ | ⚠️ Mixed | Prompt 1 empty output; prompt 2 incomplete; prompt 3 completed |
| GPT-OSS-120b | 0.11.2+rhai5 | ✅ | ⚠️ Mixed | Prompt 2 incomplete; prompts 1 and 3 completed |

## Analysis

- Note whether each model triggers `web_search` when needed.
- Compare citation quality and response completeness across model size and vLLM version.
- Highlight any failures to trigger search or improper use of results.

Run output and full response JSON are recorded in the notebook output cells for each model.

For future runs, update the date above and replace the results summary to reflect the latest notebook output.
