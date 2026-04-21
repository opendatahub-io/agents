"""
GPT-OSS model configs for BFCL evaluation (RHOAI 3.3 vs 3.4).

Append these MODEL_CONFIG_MAPPING.update() blocks to:
  gorilla/berkeley-function-call-leaderboard/bfcl_eval/constants/model_config.py

Two routing modes:
  - vllm-direct   : OPENAI_BASE_URL=http://localhost:8000/v1  (vLLM on AWS, port-forwarded)
  - ls-vllm       : OPENAI_BASE_URL=http://localhost:8321/v1  (Llama Stack proxying to vLLM)
"""

from bfcl_eval.model_handler.api_inference.openai_response import OpenAIResponsesHandler
from bfcl_eval.constants.model_config import ModelConfig, MODEL_CONFIG_MAPPING


######  ======= vLLM DIRECT - Responses API ========= #######

## gpt-oss-20b
MODEL_CONFIG_MAPPING.update({
    "vllm-direct-resp/gpt-oss-20b": ModelConfig(
        model_name="openai/gpt-oss-20b",
        display_name="openai/gpt-oss-20b vLLM Direct Responses",
        url="https://huggingface.co/openai/gpt-oss-20b",
        org="OpenAI",
        license="apache-2.0",
        model_handler=OpenAIResponsesHandler,
        input_price=None,
        output_price=None,
        is_fc_model=True,
        underscore_to_dot=True,
    ),
})

## gpt-oss-120b
MODEL_CONFIG_MAPPING.update({
    "vllm-direct-resp/gpt-oss-120b": ModelConfig(
        model_name="openai/gpt-oss-120b",
        display_name="openai/gpt-oss-120b vLLM Direct Responses",
        url="https://huggingface.co/openai/gpt-oss-120b",
        org="OpenAI",
        license="apache-2.0",
        model_handler=OpenAIResponsesHandler,
        input_price=None,
        output_price=None,
        is_fc_model=True,
        underscore_to_dot=True,
    ),
})


######  ======= LLAMA STACK -> vLLM - Responses API ========= #######

## gpt-oss-20b
MODEL_CONFIG_MAPPING.update({
    "ls-vllm-resp/gpt-oss-20b": ModelConfig(
        model_name="vllm/openai/gpt-oss-20b",
        display_name="openai/gpt-oss-20b Llama Stack -> vLLM Responses",
        url="https://huggingface.co/openai/gpt-oss-20b",
        org="OpenAI",
        license="apache-2.0",
        model_handler=OpenAIResponsesHandler,
        input_price=None,
        output_price=None,
        is_fc_model=True,
        underscore_to_dot=True,
    ),
})

## gpt-oss-120b
MODEL_CONFIG_MAPPING.update({
    "ls-vllm-resp/gpt-oss-120b": ModelConfig(
        model_name="vllm/openai/gpt-oss-120b",
        display_name="openai/gpt-oss-120b Llama Stack -> vLLM Responses",
        url="https://huggingface.co/openai/gpt-oss-120b",
        org="OpenAI",
        license="apache-2.0",
        model_handler=OpenAIResponsesHandler,
        input_price=None,
        output_price=None,
        is_fc_model=True,
        underscore_to_dot=True,
    ),
})
