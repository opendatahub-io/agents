# Validation vLLM

This folder contains validation notebooks for any models through vLLM main branch with Llama Stack APIs - Responses and Chat Completions.

## Structure

```
validation-vllm/
└── gpt-oss/
    └── function-tool-calling-responses/   # Function tool calling via Responses API
    └── function-tool-calling-chatcompletions/   # Function tool calling via Chat Completions API
```

## Tests

| Test | Models | Status |
|------|--------|--------|
| [Function Tool Calling (Responses API)](gpt-oss/function-tool-calling-responses/) | GPT-OSS-20b, GPT-OSS-120b | ✅ Passed |
| [Function Tool Calling (Chat Completions API)](gpt-oss/function-tool-calling-chatcompletions/) | GPT-OSS-20b, GPT-OSS-120b | ✅ Passed |