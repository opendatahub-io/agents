# Validate Web Search Tool Calling with GPT-OSS via Responses API (RHAIENG-2241)

## Objective

Manually test that GPT-OSS models can correctly trigger and use web search results through the Llama Stack Responses API.

## Test Results

### 2026-01-31 Run (After BRAVE_SEARCH_API_KEY Configuration)

✅ **GPT-OSS-20b** with **vLLM 0.11.2+rhai5**: 
- Prompt 1: ✅ Completed with 4 search calls (all completed, 0 failed). Response status: completed. Response text: 1,192 chars.
- Prompt 2: ⚠️ Completed with 3 search calls (2 completed, 1 failed). Response status: completed. Response text: 0 chars (empty - parsing error).
- Prompt 3: ⚠️ Completed with 7 search calls (5 completed, 2 failed). Response status: completed. Response text: 0 chars (empty - parsing error).

**Note:** After configuring `BRAVE_SEARCH_API_KEY` from `~/.profile`, web searches are executing successfully. Total: 11 searches completed, 3 failed. Prompt 1 generated a full response (1,192 chars), but Prompts 2 and 3 returned empty responses due to a server-side parsing error: `RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`. This is a Llama Stack bug where the response parser fails to handle certain vLLM response formats, even though the model successfully generates the response text.

## Setup

1. **vLLM**: Start GPT-OSS models on the target vLLM versions (e.g., `0.11.2+rhai5`)
2. **Llama Stack**: Ensure the Responses API is exposed (example: `http://127.0.0.1:8321`)
3. **Web Search**: Configure Brave Search API key in the Llama Stack server environment (e.g., `BRAVE_SEARCH_API_KEY`)
4. **.env**: Set `LLAMA_STACK_URL=http://127.0.0.1:8321` (or rely on notebook defaults)

## Test Matrix

| Model | vLLM Version |
|------|---------------|
| GPT-OSS-20b | 0.11.2+rhai5 |

## Notebooks

| Notebook | Model | vLLM Version |
|----------|-------|--------------|
| [`GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb`](./GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb) | GPT-OSS-20b | 0.11.2+rhai5 |

## Test Scenarios (Prompts)

Use prompts that require recent information so the model must invoke web search:

1. "What were the top 3 headlines about NVIDIA in the last 7 days? Include sources."
2. "What is the latest stable release of vLLM and its release date? Cite sources."
3. "What is the most recent U.S. CPI (inflation) release and its month-over-month value? Cite sources."

## Python Snippet (Responses API + Web Search)

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://127.0.0.1:8321")
response = client.responses.create(
    model="vllm/openai/gpt-oss-20b",
    tools=[{"type": "web_search"}],
    input="What were the top 3 headlines about NVIDIA in the last 7 days? Include sources.",
    max_tool_calls=50,
    max_infer_iters=50
)
print(response.output_text)
```

**Note:** Using `llama_stack_client` instead of `openai` client to support `max_infer_iters` parameter, which controls the total number of iterations (tool calls + final message generation).

## Results Summary

### 2026-01-31 Run (After BRAVE_SEARCH_API_KEY Configuration)

| Model | vLLM Version | Web Search Triggered | Result Quality | Notes |
|------|---------------|----------------------|----------------|-------|
| GPT-OSS-20b | 0.11.2+rhai5 | ✅ | ⚠️ Partial | All 3 prompts completed with web search calls executing. Total: 11 searches completed, 3 failed. Prompt 1 generated full response (1,192 chars), but Prompts 2 and 3 returned empty responses due to Llama Stack parsing error (`RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`). The model IS generating responses (visible in error logs), but Llama Stack's parser fails to handle certain vLLM response formats. Brave Search API key is working and web search integration is functional. |

## Analysis

### Key Findings (2026-01-31 - After API Key Configuration)

- **API Key Configuration**: After sourcing `~/.profile` to load `BRAVE_SEARCH_API_KEY`, web searches are now executing successfully.
- **Search Execution**: Web search calls are completing successfully (11 completed, 3 failed out of 14 total).
- **Test Results**: All 3 prompts completed with status "completed", but response quality varies:
  - Prompt 1: Full response generated (1,192 chars) with 4 successful searches
  - Prompt 2: Empty response (0 chars) despite 2 successful searches - **Llama Stack parsing error**
  - Prompt 3: Empty response (0 chars) despite 5 successful searches - **Llama Stack parsing error**
- **Response Parsing Bug**: Prompts 2 and 3 reveal a **server-side bug in Llama Stack**: The model IS generating responses (text visible in error logs), but Llama Stack's response parser fails with `RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`. This is a compatibility issue between vLLM's response format and Llama Stack's parser.

### Issues Filed

Based on testing in this session, the following issues were filed with Llama Stack:

- **[Issue #4807](https://github.com/llamastack/llama-stack/issues/4807)**: Response Parsing Error with vLLM - Some responses fail to parse correctly, resulting in empty `output_text` despite successful search calls.
- **[Issue #4781](https://github.com/llamastack/llama-stack/issues/4781)**: Unsupported tool call handling - Models may hallucinate non-existent tools, causing 500 errors.

Run output and full response JSON are recorded in the notebook output cells.
