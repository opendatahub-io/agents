#!/usr/bin/env python3

import os
import logging
from openai import OpenAI

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get token from environment
    token = os.getenv("KUBE_TOKEN", "").strip()
    if not token:
        logger.fatal("Please set KUBE_TOKEN in env")
        exit(1)

    model = "Qwen/Qwen3-0.6B"
    logger.info(f"Using model {model}")

    # Initialize OpenAI client
    client = OpenAI(base_url="http://localhost:8321/v1/openai/v1", api_key="fake")

    # Prepare the request parameters
    tools=[
        {
            "type": "mcp",
            "server_label": "kubernetes",
            "server_url": "http://localhost:8080/sse",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        },
    ]

    # Make the request using responses.create()
    try:
        response = client.responses.create(
            model=model,
            # input="Using the tool provided, list all pods in the demo-auth namespace",
            input="Using the tool provided, list all pods in the kube-system namespace",
            tools=tools
        )

        # Print the response
        print(response.output_text)

    except Exception as e:
        logger.fatal(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
