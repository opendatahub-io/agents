# Validate Web Search Tool Calling with GPT-OSS via Responses API (RHAIENG-2241)

## Objective

Manually test that GPT-OSS models can correctly trigger and use web search results through the Llama Stack Responses API.

## Test Results

### 2026-01-31 Run (GPT-OSS-20b)

✅ **GPT-OSS-20b** with **vLLM 0.11.2+rhai5**: 
- Prompt 1: ✅ Completed with 4 search calls (all completed, 0 failed). Response status: completed. Response text: 1,192 chars.
- Prompt 2: ⚠️ Completed with 3 search calls (2 completed, 1 failed). Response status: completed. Response text: 0 chars (empty - parsing error).
- Prompt 3: ⚠️ Completed with 7 search calls (5 completed, 2 failed). Response status: completed. Response text: 0 chars (empty - parsing error).

**Note:** After configuring `BRAVE_SEARCH_API_KEY` from `~/.profile`, web searches are executing successfully. Total: 11 searches completed, 3 failed. Prompt 1 generated a full response (1,192 chars), but Prompts 2 and 3 returned empty responses due to a server-side parsing error: `RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`. This is a Llama Stack bug where the response parser fails to handle certain vLLM response formats, even though the model successfully generates the response text. (see https://github.com/llamastack/llama-stack/issues/4807)

### 2026-02-01 Run (GPT-OSS-120b)

✅ **GPT-OSS-120b** with **vLLM 0.11.2+rhai5** (max_tool_calls=15, max_infer_iters=20): 
- Prompt 1: ✅ Completed with 15 search calls (all completed, 0 failed). Response status: completed. Response text: 2,301 chars.
- Prompt 2: ⚠️ Completed with 15 search calls (14 completed, 1 failed). Response status: completed. Response text: 881 chars. **Note:** Response contains incorrect date information (claimed vLLM v0.15.0 released "29 January 2024" - likely model hallucination).
- Prompt 3: ✅ Completed with 15 search calls (all completed, 0 failed). Response status: completed. Response text: 845 chars.

**Note:** Prompts 1 and 3 completed successfully with full response text. Prompt 2 generated a response but contains factually incorrect information about the vLLM release date (model issue, not parsing issue). The `max_tool_calls=15` configuration works well, leaving sufficient iterations for final message generation. Full response JSON metadata with complete output structure and text is available in the notebook for all prompts.

## Setup

1. **vLLM**: Start GPT-OSS models on the target vLLM versions (e.g., `0.11.2+rhai5`)
2. **Llama Stack**: Ensure the Responses API is exposed (example: `http://127.0.0.1:8321`)
3. **Web Search**: Configure Brave Search API key in the Llama Stack server environment (e.g., `BRAVE_SEARCH_API_KEY`)
4. **.env**: Set `LLAMA_STACK_URL=http://127.0.0.1:8321` (or rely on notebook defaults)

## Test Matrix

| Model | vLLM Version |
|------|---------------|
| GPT-OSS-20b | 0.11.2+rhai5 |
| GPT-OSS-120b | 0.11.2+rhai5 |

## Notebooks

| Notebook | Model | vLLM Version |
|----------|-------|--------------|
| [`GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb`](./GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb) | GPT-OSS-20b | 0.11.2+rhai5 |
| [`GPT-OSS-120b_with_vLLM_0.11.2+rhai5.ipynb`](./GPT-OSS-120b_with_vLLM_0.11.2+rhai5.ipynb) | GPT-OSS-120b | 0.11.2+rhai5 |

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

### 2026-01-31 Run (GPT-OSS-20b)

| Model | vLLM Version | Web Search Triggered | Result Quality | Notes |
|------|---------------|----------------------|----------------|-------|
| GPT-OSS-20b | 0.11.2+rhai5 | ✅ | ⚠️ Partial | All 3 prompts completed with web search calls executing. Total: 11 searches completed, 3 failed. Prompt 1 generated full response (1,192 chars), but Prompts 2 and 3 returned empty responses due to Llama Stack parsing error (`RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`). The model IS generating responses (visible in error logs), but Llama Stack's parser fails to handle certain vLLM response formats. Brave Search API key is working and web search integration is functional. |

### 2026-02-01 Run (GPT-OSS-120b)

| Model | vLLM Version | Web Search Triggered | Result Quality | Notes |
|------|---------------|----------------------|----------------|-------|
| GPT-OSS-120b | 0.11.2+rhai5 | ✅ | ⚠️ Partial | Prompts 1 and 3 completed successfully with full response text. Prompt 2 generated response (881 chars) but contains incorrect date information (model hallucination - claimed vLLM v0.15.0 released "29 January 2024"). Prompt 1: 2,301 chars (15 searches), Prompt 2: 881 chars (14 completed, 1 failed), Prompt 3: 845 chars (15 searches). Total: 44 searches completed, 1 failed. Using `max_tool_calls=15` and `max_infer_iters=20` provides good balance. Full JSON metadata with complete response structure and text available in notebook. |

## Analysis

### Key Findings (2026-01-31 - GPT-OSS-20b)

- **API Key Configuration**: After sourcing `~/.profile` to load `BRAVE_SEARCH_API_KEY`, web searches are now executing successfully.
- **Search Execution**: Web search calls are completing successfully (11 completed, 3 failed out of 14 total).
- **Test Results**: All 3 prompts completed with status "completed", but response quality varies:
  - Prompt 1: Full response generated (1,192 chars) with 4 successful searches
  - Prompt 2: Empty response (0 chars) despite 2 successful searches - **Llama Stack parsing error**
  - Prompt 3: Empty response (0 chars) despite 5 successful searches - **Llama Stack parsing error**
- **Response Parsing Bug**: Prompts 2 and 3 reveal a **server-side bug in Llama Stack**: The model IS generating responses (text visible in error logs), but Llama Stack's response parser fails with `RuntimeError: OpenAI response failed: unexpected tokens remaining in message header`. This is a compatibility issue between vLLM's response format and Llama Stack's parser.

### Key Findings (2026-02-01 - GPT-OSS-120b)

- **Configuration**: Using `max_tool_calls=15` and `max_infer_iters=20` provides good balance, leaving sufficient iterations for final message generation.
- **Test Results**: 
  - Prompt 1: 2,301 chars with 15 successful searches - ✅ Full response with accurate information
  - Prompt 2: 881 chars with 14 successful searches (1 failed) - ⚠️ **Response contains incorrect date information**: Model claimed vLLM v0.15.0 was released "29 January 2024", which appears to be incorrect. This is a **model hallucination issue**, not a parsing issue (Llama Stack parsed the response correctly).
  - Prompt 3: 845 chars with 15 successful searches - ✅ Full response with accurate information
- **Search Execution**: Total of 44 searches completed, 1 failed. Some "Tool execution failed" messages appear in logs, but the model retries with different queries and eventually succeeds.
- **Model Accuracy Issue**: Prompt 2 demonstrates that while the model can successfully use web search and generate responses, it may still produce factually incorrect information. This highlights the importance of fact-checking model outputs, especially for time-sensitive information like release dates.
- **Full Metadata**: Complete JSON metadata with response text is available in the notebook for all prompts.

### Issues Filed

Based on testing in this session, the following issues were filed with Llama Stack:

- **[Issue #4807](https://github.com/llamastack/llama-stack/issues/4807)**: Response Parsing Error with vLLM - Some responses fail to parse correctly, resulting in empty `output_text` despite successful search calls.
- **[Issue #4781](https://github.com/llamastack/llama-stack/issues/4781)**: Unsupported tool call handling - Models may hallucinate non-existent tools, causing 500 errors.

Run output and full response JSON are recorded in the notebook output cells.
