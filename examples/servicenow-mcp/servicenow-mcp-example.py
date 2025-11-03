import os
from openai import OpenAI


PROMPT = "Using the tool provided, summarize the five most recent incidents."


def main():
    model = os.getenv("INFERENCE_MODEL", "gpt-4o")
    print(f"Using model {model}")

    client = OpenAI()
    response = client.responses.create(
        model=model,
        tools=[
            {
                "type": "mcp",
                "server_label": "servicenow",
                "server_url": f"http://127.0.0.1:3333/sse",
                "allowed_tools": ["list_incidents"],
            }
        ],
        input=PROMPT,
    )

    print(response.output_text)


if __name__ == "__main__":
    main()
