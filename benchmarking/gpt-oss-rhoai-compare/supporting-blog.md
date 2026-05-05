# Your inference stack matters more than you think

Any real deployment has an API layer between the application and the inference engine -- to swap models without rewriting code, centralize auth, add caching. Every request passes through it:

`Client -> API layer -> inference server -> API layer -> client`

The assumption is that the API layer passes everything through faithfully. But it can [pass tool schemas incorrectly](https://github.com/BerriAI/litellm/issues/19741), handle fields differently across versions, or drop state that carries conversation context -- so the final prompt the model sees differs from the format it was trained on. In multi-turn tool calling, the client takes the response, updates conversation history, and sends it back through the API layer for the next turn. If information is silently lost, there are no failing tests, just quiet accuracy loss. That's one of the reasons we hear widely varying opinions on performance of SOTA agentic models.

The only way to catch this is end-to-end evaluation: running a benchmark like BFCL across your full stack and comparing the numbers against direct calls from your application to the inference provider.

## Our stack: OGX + vLLM

[OGX](https://github.com/ogx-ai/ogx) is an open source API server that gives you a single OpenAI-compatible interface and lets you swap between inference providers -- [vLLM](https://github.com/vllm-project/vllm), Ollama, Bedrock, or others -- without changing application code. RHOAI ships both together.

We ran the [Berkeley Function Calling Leaderboard (BFCL)](https://gorilla.cs.berkeley.edu/leaderboard.html) for [GPT-OSS](https://openai.com/index/introducing-gpt-oss/) model on this stack across RHOAI 3.3 and 3.4. The surprise was not that 3.4 scored better, but *where* the gain came from. Notably, upgrading OGX without vLLM made things worse -- a regression that would have been invisible without the benchmark.

GPT-OSS-120b on RHOAI 3.4 scored **51.4%** on BFCL multi-turn, up from **44.8%** on 3.3 -- a 6.6 percentage point gain in tool-calling accuracy across multi-step conversations.

RHOAI tests OGX and vLLM together before shipping, so a version bump in one does not silently break the other. If you run your own stack with different in-between layers, the same lesson applies: test end-to-end. 

## Where the gain came from

The two components driving accuracy gains in RHOAI 3.4 are [vLLM](https://github.com/vllm-project/vllm) ([v0.13.0](https://github.com/vllm-project/vllm/tree/v0.13.0) to [v0.18.0](https://github.com/vllm-project/vllm/tree/v0.18.0)) and [OGX](https://ogx-ai.github.io/blog/from-llama-stack-to-ogx) ([v0.4.2](https://github.com/opendatahub-io/ogx/tree/v0.4.2.1%2Brhai0) to [v0.7.1](https://github.com/opendatahub-io/ogx/tree/v0.7.1%2Brhaiv.1)). The BFCL tests run through OGX's [Responses API](https://ogx-ai.github.io/blog/responses-api), with the BFCL harness managing the multi-turn tool-calling loop client-side.

We tested every combination of old and new:

| Configuration | Overall Accuracy |
|---|---|
| RHOAI 3.3 OGX + RHOAI 3.3 vLLM | 44.8% |
| RHOAI 3.3 OGX + RHOAI 3.4 vLLM | 46.0% |
| RHOAI 3.4 OGX + RHOAI 3.3 vLLM | 43.6% |
| RHOAI 3.4 OGX + RHOAI 3.4 vLLM | **51.4%** |

Neither upgrade helped much alone -- OGX-only actually regressed. Both together jumped to 51.4%. The pieces have to move together.

Full results, including GPT-OSS-20b and vLLM-direct baselines, are in the [benchmark report](https://github.com/opendatahub-io/agents/tree/main/benchmarking/gpt-oss-rhoai-compare#2-results).


## Reproduce it yourself

The [benchmark report](https://github.com/opendatahub-io/agents/tree/main/benchmarking/gpt-oss-rhoai-compare) has step-by-step instructions to replicate the results, including OGX and vLLM versions, BFCL test setup, and evaluation commands. We recommend a GPU node equivalent to AWS `g6e.12xlarge` to serve the models.

To get started with RHOAI 3.4, see the [Red Hat OpenShift AI documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai). The [BFCL benchmark](https://gorilla.cs.berkeley.edu/leaderboard.html) is open source if you want to run it against your own stack.
