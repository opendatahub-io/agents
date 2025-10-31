import os
from openai import OpenAI


PROMPT = "Using the tool provided, summarize the five most recent incidents."


def main():
    model = os.getenv("INFERENCE_MODEL", "openai/gpt-4o")
    print(f"Using model {model}")

    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8321/v1/openai/v1")
    client = OpenAI(base_url=base_url)
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
