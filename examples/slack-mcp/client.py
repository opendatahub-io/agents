import os

from openai import OpenAI


PROMPT = "Using the slack mcp tool provided, list all the channels you are in."


def main():
    model = os.getenv("INFERENCE_MODEL", "gpt-4o-mini")
    print(f"Using model: {model}")

    slack_token = os.getenv("SLACK_MCP_TOKEN")
    if not slack_token:
        raise ValueError("SLACK_MCP_TOKEN environment variable is not set")

    client = OpenAI()
    response = client.responses.create(
        model=model,
        tools=[
            {
                "type": "mcp",
                "server_label": "slack",
                "server_url": "http://127.0.0.1:13080/sse",
                "headers": {
                    "Authorization": f"Bearer {slack_token}"
                }

            }
        ],
        input=PROMPT,
    )

    print(response.output_text)


if __name__ == "__main__":
    main()
