"""LLM configuration with Llama Stack / OpenAI toggle.

This module provides a factory function to get the appropriate LLM instance
based on the USE_LLAMA_STACK environment variable.

Environment Variables:
    USE_LLAMA_STACK: "true" for Llama Stack, "false" for OpenAI (default: "true")
    LLAMA_STACK_URL: Llama Stack server URL (default: "http://localhost:8321")
    MODEL_NAME: Model identifier for Llama Stack (default: "openai/gpt-4o")
    OPENAI_API_KEY: OpenAI API key (required if USE_LLAMA_STACK=false)
    OPENAI_MODEL: OpenAI model name (default: "gpt-4o")
"""

import os

from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    """Get LLM instance based on environment configuration.

    Returns:
        ChatOpenAI: Configured LLM instance for either Llama Stack or OpenAI.

    Examples:
        # Using Llama Stack (default):
        export LLAMA_STACK_URL=http://localhost:8321

        # Using OpenAI directly:
        export USE_LLAMA_STACK=false
        export OPENAI_API_KEY=your-api-key
    """
    use_llama_stack = os.getenv("USE_LLAMA_STACK", "true").lower() == "true"

    if use_llama_stack:
        # Use Llama Stack endpoint (OpenAI-compatible API)
        llama_stack_url = os.getenv("LLAMA_STACK_URL", "http://localhost:8321")
        model_name = os.getenv("MODEL_NAME", "openai/gpt-4o")

        print(f"[LLM] Using Llama Stack at {llama_stack_url}")
        print(f"[LLM] Model: {model_name}")

        return ChatOpenAI(
            base_url=f"{llama_stack_url}/v1",
            api_key="not-needed",  # Llama Stack doesn't require API key
            model=model_name,
        )
    else:
        # Use OpenAI directly
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when USE_LLAMA_STACK=false"
            )

        print(f"[LLM] Using OpenAI directly")
        print(f"[LLM] Model: {model}")

        return ChatOpenAI(
            api_key=api_key,
            model=model,
        )
