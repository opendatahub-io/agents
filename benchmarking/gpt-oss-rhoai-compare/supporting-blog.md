# Your inference stack matters more than you think

If you are running agentic workloads in production, you want an API layer between your application and the inference engine for things like swapping providers without rewriting code, managing multi-turn conversation state, and observability. Every request passes through it:

`Client -> API layer -> inference server -> API layer -> client`

You would expect this layer to pass everything through faithfully. But it can [pass tool schemas incorrectly](https://github.com/BerriAI/litellm/issues/19741), handle fields differently across versions, or drop state that carries conversation context. When that happens, the final prompt the model sees differs from the format it was trained on. In multi-turn tool calling, the client takes the response, updates conversation history, and sends it back through the API layer for the next turn. If information is silently lost, there are no failing tests, just quiet accuracy loss. This is one reason performance reports for the same agentic model vary so widely across different deployments.

The only way to catch this is to run an end-to-end benchmark like [BFCL](https://gorilla.cs.berkeley.edu/leaderboard.html) across your full stack and compare the numbers against direct calls to the inference provider.

## Our stack: OGX + vLLM

[OGX](https://github.com/ogx-ai/ogx) is an open source API server that provides a single OpenAI-compatible interface across multiple inference providers, including [vLLM](https://github.com/vllm-project/vllm), Ollama, and Bedrock. Red Hat OpenShift AI (RHOAI) ships both together.

We ran BFCL for [GPT-OSS](https://openai.com/index/introducing-gpt-oss/), OpenAI's open-weight model family, on this stack across RHOAI 3.3 and 3.4. The surprise was not that 3.4 scored better, but *where* the gain came from. Upgrading OGX without vLLM actually made things worse, a regression that would have been invisible without the benchmark.

GPT-OSS-120b on RHOAI 3.4 scored **51.4%** on BFCL multi-turn, up from **44.8%** on 3.3: a 6.6 percentage point gain in tool-calling accuracy across multi-step conversations.

RHOAI tests OGX and vLLM together before shipping, so a version bump in one does not silently break the other. That means your team can focus on building applications instead of debugging invisible regressions between infrastructure components. And when the next round of model and infrastructure improvements ships, you get those gains without re-qualifying each piece yourself. If you run your own stack with different layers in between, the same lesson applies: test end-to-end.

## Where the gain came from

Among many changes in RHOAI 3.4, the two driving accuracy gains in these experiments are [vLLM](https://github.com/vllm-project/vllm) ([v0.13.0](https://github.com/vllm-project/vllm/tree/v0.13.0) to [v0.18.0](https://github.com/vllm-project/vllm/tree/v0.18.0)) and [OGX](https://ogx-ai.github.io/blog/from-llama-stack-to-ogx) ([v0.4.2](https://github.com/opendatahub-io/ogx/tree/v0.4.2.1%2Brhai0) to [v0.7.1](https://github.com/opendatahub-io/ogx/tree/v0.7.1%2Brhaiv.1)). The BFCL tests run through OGX's [Responses API](https://ogx-ai.github.io/blog/responses-api), with the BFCL harness managing the multi-turn tool-calling loop client-side.

We tested every combination of old and new:

| Configuration | Overall Accuracy |
|---|---|
| RHOAI 3.3 OGX + RHOAI 3.3 vLLM | 44.8% |
| RHOAI 3.3 OGX + RHOAI 3.4 vLLM | 46.0% |
| RHOAI 3.4 OGX + RHOAI 3.3 vLLM | 43.6% |
| RHOAI 3.4 OGX + RHOAI 3.4 vLLM | **51.4%** |

Upgrading vLLM alone gave a small bump. Upgrading OGX alone actually regressed. Both together jumped to 51.4%. The pieces have to move together.

Full results, including GPT-OSS-20b and vLLM-direct baselines, are in the [benchmark report](https://github.com/opendatahub-io/agents/tree/main/benchmarking/gpt-oss-rhoai-compare#2-results).

## Reproduce it yourself

The [benchmark report](https://github.com/opendatahub-io/agents/tree/main/benchmarking/gpt-oss-rhoai-compare) has step-by-step instructions to replicate the results, including OGX and vLLM versions, BFCL test setup, and evaluation commands. GPT-OSS-120b uses MXFP4 quantization and fits on a single 80GB GPU, but for production serving we recommend a multi-GPU setup such as 4x NVIDIA H100 with NVLink. We ran our tests on an AWS `g6e.12xlarge` (4x NVIDIA L40S). See the [vLLM GPT-OSS recipe](https://docs.vllm.ai/projects/recipes/en/latest/OpenAI/GPT-OSS.html) for detailed hardware guidance.

To get started with RHOAI 3.4, see the [Red Hat OpenShift AI documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai). The [BFCL benchmark](https://gorilla.cs.berkeley.edu/leaderboard.html) is open source if you want to run it against your own stack.
