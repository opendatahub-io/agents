## Plan of Action 
- [This](https://docs.google.com/spreadsheets/d/1DkRy2g_p95Ju25xj0fT8cDHml1GXfWISYTXOqUs3a7w/edit?usp=sharing) Spreadsheet lists corresponding versions of llamastack shipped with RHOAI 3.3 and 3.4
- [This](https://docs.google.com/spreadsheets/d/17GnTfbYP2nE36VF4LXIBVQeXRGh3fUJmqyNUnSFb9bQ/edit?usp=sharing) is corresponding one for vllm-rhoai mapping

| RHOAI target version | LLS rhoai version | VLLM rhoai version |
|---|---|---|
| 3.3 | [0.4.2.1+rhai0](https://gitlab.com/redhat/rhel-ai/llama-stack/pipeline/-/releases/3.3.932+llama-stack-cpu-ubi9-aarch64) | v0.13.0 |
| 3.4 | [v0.7.1+rhaiv.1](https://gitlab.com/redhat/rhel-ai/llama-stack/pipeline/-/releases/3.4.1341+llama-stack-cpu-ubi9-ppc64le) | 0.18.0 |



## Project Repos

### Setup

Clone the repos needed locally (Llama Stack + Gorilla). vLLM is built on the AWS instance — see [vLLM Setup (AWS)](#vllm-setup-aws).

```bash
# RHOAI 3.3
mkdir -p rhoai_3.3
git clone --depth 1 --branch '0.4.2.1+rhai0' https://github.com/opendatahub-io/llama-stack.git rhoai_3.3/llama-stack

# RHOAI 3.4
mkdir -p rhoai_3.4
git clone --depth 1 --branch 'v0.7.1+rhaiv.1' https://github.com/opendatahub-io/llama-stack.git rhoai_3.4/llama-stack

# BFCL Gorilla
git clone https://github.com/ShishirPatil/gorilla.git gorilla
cd gorilla && git checkout 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8 && cd ..
```

Local folder structure:

```
├── rhoai_3.3/
│   └── llama-stack/   (tag 0.4.2.1+rhai0)
├── rhoai_3.4/
│   └── llama-stack/   (tag v0.7.1+rhaiv.1)
└── gorilla/           (commit 6ea5797)
```

### Source Links

**RHOAI 3.3**
- [llama-stack](https://github.com/opendatahub-io/llama-stack/tree/0.4.2.1%2Brhai0) — tag `0.4.2.1+rhai0`

**RHOAI 3.4**
- [llama-stack](https://github.com/opendatahub-io/llama-stack/tree/v0.7.1%2Brhaiv.1) — tag `v0.7.1+rhaiv.1`

**vLLM** (built on AWS)
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

```
gorilla/berkeley-function-call-leaderboard/bfcl_eval/constants/model_config.py
```

This registers 4 model keys:

| Key | Routes through | `model_name` sent to server |
|---|---|---|
| `vllm-direct-resp/gpt-oss-20b` | vLLM directly | `openai/gpt-oss-20b` |
| `vllm-direct-resp/gpt-oss-120b` | vLLM directly | `openai/gpt-oss-120b` |
| `ls-vllm-resp/gpt-oss-20b` | Llama Stack -> vLLM | `vllm/openai/gpt-oss-20b` |
| `ls-vllm-resp/gpt-oss-120b` | Llama Stack -> vLLM | `vllm/openai/gpt-oss-120b` |

### Manually Pass reasoning effort to responses api

This is a no-op for vLLM direct calls but required for Llama Stack to correctly forward reasoning output back as input in subsequent turns.

```
gorilla/berkeley-function-call-leaderboard/bfcl_eval/model_handler/api_inference/openai_response.py
```

```python
@retry_with_backoff(error_type=RateLimitError)
def generate_with_backoff(self, **kwargs):
    start_time = time.time()
    kwargs['reasoning'] = {"effort": "medium"}  # <-- add this line
    api_response = self.client.responses.create(**kwargs)
```



## vLLM Setup (AWS)

Follow the [GPT-OSS on AWS guide](https://docs.google.com/document/d/1y04AuNbeFIHBwaDZgbrMbq20MqajLp_LrBUtrcrBSJE/edit?usp=sharing) for AWS provisioning on GPU node, and port forwarding. The only change is cloning the version-specific vllm repo instead of upstream.

On the AWS instance:
```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone the version-specific vllm
git clone --depth 1 --branch v0.13.0 https://github.com/vllm-project/vllm.git   # RHOAI 3.3
# or
git clone --depth 1 --branch v0.18.0 https://github.com/vllm-project/vllm.git   # RHOAI 3.4

# 3. Build from source (~20 min)
cd vllm
uv venv --python 3.12 --seed
source .venv/bin/activate
# Took an Hour
uv pip install --editable .
```

### Serve the model (on the AWS instance)

```bash
# gpt-oss-120b
vllm serve openai/gpt-oss-120b \ # or openai/gpt-oss-20b
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 4 \
    --max-model-len 8192 \
    --enable-auto-tool-choice \
    --tool-call-parser openai
```

Now port forwarding as per guide. vLLM will be available at `localhost:8000` for Llama Stack to connect to via `VLLM_URL=http://localhost:8000/v1`.

## Llama Stack Setup

Repeat for each version (`rhoai_3.3`, `rhoai_3.4`). The install process is the same for both.

### 1. Create venv and install from source

```bash
cd rhoai_3.3/llama-stack   # or rhoai_3.4/llama-stack
uv venv --python=3.12
source .venv/bin/activate
uv pip install -e .
uv run llama stack list-deps starter | xargs -L1 uv pip install
VLLM_URL=http://localhost:8000/v1 uv run llama stack run starter
```

### Docs reference

For more details on setup and usage, build the docs locally for each version:

```bash
cd <rhoai_version>/llama-stack/docs
npm install
npm run gen-api-docs all
npm run build
npm run serve   # opens at http://localhost:3000
```

- **RHOAI 3.3**: See `rhoai_3.3/llama-stack/docs/docs/getting_started/detailed_tutorial.mdx`
- **RHOAI 3.4**: See `rhoai_3.4/llama-stack/docs/docs/getting_started/detailed_tutorial.mdx`

### Troubleshooting: 

Noticed an error like this due to stale registry from a previous Llama Stack run :
```
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

**A. vLLM direct** (port-forwarded from AWS on `:8000`):

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

**B. Llama Stack -> vLLM** (Llama Stack on `:8321`, proxying to vLLM):

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

### 2. Results (BFCL Multi-Turn, GPT-OSS-120b)

Table added [here](https://docs.google.com/document/d/1zZRE9zKxuYeDHnCyrnObY23nmvrIcT4qbn9k0-CAd8s/edit?usp=sharing) for ease of discussion.


Same Result Copied here : 
**Llama Stack + vLLM (what customers get)**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 LS + RHOAI 3.3 vLLM | 44.75% | 52.00% | 52.00% | 44.00% | 31.00% |
| RHOAI 3.3 LS + RHOAI 3.4 vLLM | 46.00% | 55.50% | 49.00% | 48.00% | 31.50% |
| RHOAI 3.4 LS + RHOAI 3.3 vLLM | 43.62% | 53.00% | 44.50% | 46.50% | 30.50% |
| RHOAI 3.4 LS + RHOAI 3.4 vLLM | **51.37%** | 63.50% | 53.50% | 52.50% | 36.00% |

**vLLM direct (no Llama Stack)**

| Config | Overall Acc | Base | Miss Func | Miss Param | Long Context |
|---|---|---|---|---|---|
| RHOAI 3.3 vLLM direct | 45.75% | 60.50% | 40.50% | 48.00% | 34.00% |
| RHOAI 3.4 vLLM direct | 40.88% | 55.50% | 38.50% | 40.50% | 29.00% |



