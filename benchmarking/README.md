# Benchmarking

Below is a guide on how to run BFCL benchmarking either using vLLM directly or vLLM through Llama Stack. This includes running with models not in BFCL's supported model list and using both OpenAI's Responses and Chat Completions APIs.

```bash
# Create a new virtual environment with Python 3.12
uv venv --python=3.12

# Clone the Gorilla repository
git clone https://github.com/ShishirPatil/gorilla.git

# Change directory to the `berkeley-function-call-leaderboard`
cd gorilla/berkeley-function-call-leaderboard

# Install the package in editable mode
uv pip install -e .
```

## Using Inference Direct-to-vLLM

> Note: The below steps describe setting up vLLM as an inference server on your own GPU-enabled remote instance. Steps 1 and 2 are also needed if intending to use your own vLLM server with Llama Stack. If you have a readily available vLLM endpoint, you may skip to step 3.

1. On your remote instance, install and run vLLM

```bash
uv venv --python=3.12
uv pip install vllm

vllm serve openai/gpt-oss-120b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 4 \
    --max-model-len 8192 \
    --enable-auto-tool-choice \
    --tool-call-parser openai
```

2. On your local machine, setup port-forwarding to your remote instance

```bash
ssh -N -f -L 8000:localhost:8000 <remote-user>@<remote-url>
```

3. Additionally, set the necessary OpenAI environment variables

```bash
# point BFCL towards vLLM
export OPENAI_BASE_URL=http://localhost:8000/v1

# Populate OPENAI_API_KEY (No token is needed but OpenAI Client will complain if unset)
OPENAI_API_KEY=EMPTY
```

## Using Inference Through Llama Stack (to vLLM)

In a separate terminal instance, install Llama Stack:

```bash
uv venv --python=3.12

uv pip install llama-stack
```

> Note: The provided Llama Stack `config.yaml` specifies `http://localhost:8000/v1` as vLLM's base url, which is correct if you set up vLLM according to steps 1 and 2 in the previous section. If using a pre-baked endpoint, please change the base_url under vLLM's inference provider entry to your endpoint (including the trailing `/v1`). If using a different model than the ones described here, please add those entries under the `models` field.

Once you are satisfied with your config, you can run Llama Stack as follows:

```bash
# point BFCL towards Llama Stack
export OPENAI_BASE_URL=http://localhost:8321/v1

# Populate OPENAI_API_KEY (No token is needed but OpenAI Client will complain if unset)
OPENAI_API_KEY=EMPTY

# Run Llama Stack
llama stack run config.yaml
```

## Running BFCL

BFCL publishes a list of supported models. If your chosen model is not in the supported list, you will need to add it to `gorilla/berkeley-function-call-leaderboard/bfcl_eval/constants/model_config.py` (from wherever you placed the gorilla repository and pip installed bfcl as editable). Simply add the following to the end of the file:

```python
MODEL_CONFIG_MAPPING.update({
    "openai/gpt-oss-120b": ModelConfig(  # Name recognized by BFCL. Used in bfcl subcommands and path construction for results and scores
        model_name="vllm/openai/gpt-oss-120b",  # Name used by your inference server
        display_name="openai/gpt-oss-120b (FC) (Llama Stack Responses)",  # Name to be displayed in scoring tables
        url="https://huggingface.co/openai/gpt-oss-120b",
        org="OpenAI",
        license="apache-2.0",
        model_handler=OpenAIResponsesHandler,  # Or alternatively OpenAICompletionsHandler for Chat Completions
        input_price=None,
        output_price=None,
        is_fc_model=True,
        underscore_to_dot=True,
    ),
    # Similarly, you may add multiple entries for other models within this dict
})
```

### Running BFCL

You can find all available benchmark jsons at `<path-to-bfcl>/bfcl_eval/data` and their respective names accepted as test categories by inspecting `<path-to-bfcl>/bfcl_eval/constants/category_mapping.py`. For this example, we will be using `multi-turn`.

BFCL runs in two steps: Generation runs the benchmarks against your specified model and stores intermediary results in a `results/` directory, and Evaluation scores those results against the expected results and stores them in `scores/`. By default, these directories are placed in `<path-to-gorilla>/berkeley-function-call-leaderboard` if you installed from source, but you can configure where they are placed by setting `BFCL_PROJECT_ROOT` in your environment.

Generation:

```bash
bfcl generate \
  --model openai/gpt-oss-120b \
  --test-category multi_turn \
  --num-threads 8 \
--allow-overwrite
```

Evaluation:

```bash
bfcl evaluate \
  --model lls/gpt-oss-120b \
  --test-category multi_turn
```

In addition to <TODO> scores, you will see its accuracy scores populated in its respective .csv file within the `score/` subdirectory. For `multi_turn`, this is `data_multi_turn.csv`. This will be appended to with each `bfcl evaluate` you run, replacing older results for the same model in case of reruns.