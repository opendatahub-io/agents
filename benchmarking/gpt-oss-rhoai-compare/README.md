## BFCL Evaluation: GPT-OSS on RHOAI 3.3 vs 3.4

This guide covers how to reproduce the [Berkeley Function Calling Leaderboard (BFCL)](https://gorilla.cs.berkeley.edu/leaderboard.html) multi-turn evaluation of GPT-OSS models across RHOAI 3.3 and 3.4 inference stacks.

### Versions tested

| RHOAI target version | OGX rhoai version | VLLM rhoai version |
|---|---|---|
| 3.3 | [0.4.2.1+rhai0](https://github.com/opendatahub-io/ogx/tree/v0.4.2.1%2Brhai0) | [v0.13.0](https://github.com/vllm-project/vllm/tree/v0.13.0) |
| 3.4 | [v0.7.1+rhaiv.1](https://github.com/opendatahub-io/ogx/tree/v0.7.1%2Brhaiv.1) | [v0.18.0](https://github.com/vllm-project/vllm/tree/v0.18.0) |



## Project Repos

### Setup

Clone the repos needed locally (OGX + Gorilla). vLLM is built on your GPU node — see [vLLM Setup](#vllm-setup).

```bash
# RHOAI 3.3
mkdir -p rhoai_3.3
git clone --depth 1 --branch '0.4.2.1+rhai0' https://github.com/opendatahub-io/ogx.git rhoai_3.3/ogx

# RHOAI 3.4
mkdir -p rhoai_3.4
git clone --depth 1 --branch 'v0.7.1+rhaiv.1' https://github.com/opendatahub-io/ogx.git rhoai_3.4/ogx

# BFCL Gorilla
git clone https://github.com/ShishirPatil/gorilla.git gorilla
cd gorilla && git checkout 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8 && cd ..
```

Local folder structure:

```text
├── rhoai_3.3/
│   └── ogx/   (tag 0.4.2.1+rhai0)
├── rhoai_3.4/
│   └── ogx/   (tag v0.7.1+rhaiv.1)
└── gorilla/           (commit 6ea5797)
```

### Source Links

**RHOAI 3.3**
- [ogx](https://github.com/opendatahub-io/ogx/tree/0.4.2.1%2Brhai0) — tag `0.4.2.1+rhai0`

**RHOAI 3.4**
- [ogx](https://github.com/opendatahub-io/ogx/tree/v0.7.1%2Brhaiv.1) — tag `v0.7.1+rhaiv.1`

**vLLM** (built on GPU node)
- [v0.13.0](https://github.com/vllm-project/vllm/tree/v0.13.0) — RHOAI 3.3
- [v0.18.0](https://github.com/vllm-project/vllm/tree/v0.18.0) — RHOAI 3.4

**BFCL Gorilla**
- [gorilla](https://github.com/ShishirPatil/gorilla/) — pinned to commit [`6ea5797`](https://github.com/ShishirPatil/gorilla/commit/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8)



## Gorilla Repo Setup

```bash
cd gorilla
uv venv --python=3.12
source ./.venv/bin/activate
cd ./berkeley-function-call-leaderboard/
uv pip install -e .
```

### Register GPT-OSS models

The gorilla repo doesn't know about GPT-OSS models. Copy the `MODEL_CONFIG_MAPPING.update({...})` blocks from `bench_configs.py` and append them to the bottom of:

```text
gorilla/berkeley-function-call-leaderboard/bfcl_eval/constants/model_config.py
```

This registers 4 model keys:

| Key | Routes through | `model_name` sent to server |
|---|---|---|
| `vllm-direct-resp/gpt-oss-20b` | vLLM directly | `openai/gpt-oss-20b` |
| `vllm-direct-resp/gpt-oss-120b` | vLLM directly | `openai/gpt-oss-120b` |
| `ls-vllm-resp/gpt-oss-20b` | OGX -> vLLM | `vllm/openai/gpt-oss-20b` |
| `ls-vllm-resp/gpt-oss-120b` | OGX -> vLLM | `vllm/openai/gpt-oss-120b` |

### Manually Pass reasoning effort to responses api

This is a no-op for vLLM direct calls but required for OGX to correctly forward reasoning output back as input in subsequent turns.

```text
gorilla/berkeley-function-call-leaderboard/bfcl_eval/model_handler/api_inference/openai_response.py
```

```python
@retry_with_backoff(error_type=RateLimitError)
def generate_with_backoff(self, **kwargs):
    start_time = time.time()
    kwargs['reasoning'] = {"effort": "medium"}  # <-- add this line
    api_response = self.client.responses.create(**kwargs)
```



## vLLM Setup

You need a GPU node with at least 4 GPUs to serve GPT-OSS-120b (e.g., AWS `g6e.12xlarge` with 4x NVIDIA L40S). GPT-OSS-20b fits on the same hardware. Any cloud provider or bare-metal server with NVIDIA GPUs and CUDA drivers will work.

On your GPU node:

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone the version-specific vllm
git clone --depth 1 --branch v0.13.0 https://github.com/vllm-project/vllm.git   # RHOAI 3.3
# or
git clone --depth 1 --branch v0.18.0 https://github.com/vllm-project/vllm.git   # RHOAI 3.4

# 3. Build from source
cd vllm
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install --editable .
```

### Serve the model

```bash
vllm serve openai/gpt-oss-120b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 4 \
    --max-model-len 8192 \
    --enable-auto-tool-choice \
    --tool-call-parser openai
```

If the GPU node is remote, use SSH port forwarding (`ssh -L 8000:localhost:8000 user@host`) so that vLLM is available at `localhost:8000` for OGX to connect to via `VLLM_URL=http://localhost:8000/v1`.

## OGX Setup

Repeat for each version (`rhoai_3.3`, `rhoai_3.4`). The install process is the same for both.

### 1. Create venv and install from source

```bash
cd rhoai_3.3/ogx   # or rhoai_3.4/ogx
uv venv --python=3.12
source .venv/bin/activate
uv pip install -e .
uv run llama stack list-deps starter | xargs -L1 uv pip install
VLLM_URL=http://localhost:8000/v1 uv run llama stack run starter
```

### Docs reference

For more details on setup and usage, build the docs locally for each version:

```bash
cd <rhoai_version>/ogx/docs
npm install
npm run gen-api-docs all
npm run build
npm run serve   # opens at http://localhost:3000
```

- **RHOAI 3.3**: See `rhoai_3.3/ogx/docs/docs/getting_started/detailed_tutorial.mdx`
- **RHOAI 3.4**: See `rhoai_3.4/ogx/docs/docs/getting_started/detailed_tutorial.mdx`

### Troubleshooting: 

Noticed an error like this due to stale registry from a previous OGX run :
```text
ValueError: Object of type 'tool_group' and identifier 'builtin::websearch' already exists.
```

Fixed it by clearing the cached state and then re-ran.

```bash
rm ~/.llama/distributions/starter/kvstore.db
rm ~/.llama/distributions/starter/sql_store.db
```


## Running BFCL Evaluation

Reference: [opendatahub-io/agents benchmarking guide](https://github.com/opendatahub-io/agents/tree/main/benchmarking)

### 1. Run evaluations

Each run requires setting `OPENAI_BASE_URL` to point at the right server.

```bash
cd gorilla/berkeley-function-call-leaderboard
source .venv/bin/activate
```

**A. vLLM direct** (port-forwarded on `:8000`):

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=EMPTY

# gpt-oss-20b
bfcl generate --model vllm-direct-resp/gpt-oss-20b --test-category multi_turn --num-threads 8 --allow-overwrite
bfcl evaluate --model vllm-direct-resp/gpt-oss-20b --test-category multi_turn

# gpt-oss-120b
bfcl generate --model vllm-direct-resp/gpt-oss-120b --test-category multi_turn --num-threads 8 --allow-overwrite
bfcl evaluate --model vllm-direct-resp/gpt-oss-120b --test-category multi_turn
```

**B. OGX -> vLLM** (OGX on `:8321`, proxying to vLLM):

```bash
export OPENAI_BASE_URL=http://localhost:8321/v1
export OPENAI_API_KEY=EMPTY

# gpt-oss-20b
bfcl generate --model ls-vllm-resp/gpt-oss-20b --test-category multi_turn --num-threads 8 --allow-overwrite
bfcl evaluate --model ls-vllm-resp/gpt-oss-20b --test-category multi_turn

# gpt-oss-120b
bfcl generate --model ls-vllm-resp/gpt-oss-120b --test-category multi_turn --num-threads 8 --allow-overwrite
bfcl evaluate --model ls-vllm-resp/gpt-oss-120b --test-category multi_turn
```

### 2. Results

#### GPT-OSS-120b (BFCL Multi-Turn)

**OGX + vLLM (what customers get)**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 LS + RHOAI 3.3 vLLM | 44.75% | 52.00% | 52.00% | 44.00% | 31.00% |
| RHOAI 3.3 LS + RHOAI 3.4 vLLM | 46.00% | 55.50% | 49.00% | 48.00% | 31.50% |
| RHOAI 3.4 LS + RHOAI 3.3 vLLM | 43.62% | 53.00% | 44.50% | 46.50% | 30.50% |
| RHOAI 3.4 LS + RHOAI 3.4 vLLM | **51.37%** | 63.50% | 53.50% | 52.50% | 36.00% |

**vLLM direct (no OGX)**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 vLLM | 45.75% | 60.50% | 40.50% | 48.00% | 34.00% |
| RHOAI 3.4 vLLM | 40.88% | 55.50% | 38.50% | 40.50% | 29.00% |

#### GPT-OSS-20b (BFCL Multi-Turn)

**OGX + vLLM**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 LS + RHOAI 3.3 vLLM | 30.63% | 33.50% | 32.50% | 36.00% | 20.50% |
| RHOAI 3.4 LS + RHOAI 3.3 vLLM | 28.25% | 34.50% | 28.50% | 33.50% | 16.50% |
| RHOAI 3.4 LS + RHOAI 3.4 vLLM | 29.25% | 32.50% | 31.50% | 32.50% | 20.50% |

**vLLM direct (no OGX)**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 vLLM | 40.12% | 55.00% | 34.50% | 42.50% | 28.50% |
| RHOAI 3.4 vLLM | 35.62% | 46.50% | 30.00% | 40.00% | 26.00% |

---

## Internal Documentation

- [OGX ↔ RHOAI version mapping](https://docs.google.com/spreadsheets/d/1DkRy2g_p95Ju25xj0fT8cDHml1GXfWISYTXOqUs3a7w/edit?usp=sharing)
- [vLLM ↔ RHOAI version mapping](https://docs.google.com/spreadsheets/d/17GnTfbYP2nE36VF4LXIBVQeXRGh3fUJmqyNUnSFb9bQ/edit?usp=sharing)
- [Results discussion doc](https://docs.google.com/document/d/1zZRE9zKxuYeDHnCyrnObY23nmvrIcT4qbn9k0-CAd8s/edit?usp=sharing)
- [GPT-OSS on AWS provisioning guide](https://docs.google.com/document/d/1y04AuNbeFIHBwaDZgbrMbq20MqajLp_LrBUtrcrBSJE/edit?usp=sharing)