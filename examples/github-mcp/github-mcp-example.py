import os
from openai import OpenAI
# from openai.types.responses.tool_param import Mcp


PROMPT = "Using the tool provided, summarize the five most recent commits on main for the llama-stack repo owned by llamastack?"


def main():
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        raise ValueError("Please set GITHUB_TOKEN in env")

    model = os.getenv("INFERENCE_MODEL", "openai/gpt-4o")
    print(f"Using model {model}")

    client = OpenAI()

    response = client.responses.create(
        model=model,
        tools=[{
            "type": "mcp",
            "server_label": "github",
            "server_url": "https://api.githubcopilot.com/mcp/x/repos/readonly",
            "headers": {"Authorization": f"Bearer {gh_token}"}
        }],
        input=PROMPT
    )

    print(response.output_text)


if __name__ == "__main__":
    main()