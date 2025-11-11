import os

from openai import OpenAI
from google_auth_oauthlib.flow import InstalledAppFlow


PROMPT = "Using the tool provided, create a document containing a poem and return the link to it"


def main():
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not any([client_id, client_secret]):
        raise ValueError("GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in env")
    
    flow = InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ],
    )

    creds = flow.run_local_server()

    model = os.getenv("INFERENCE_MODEL", "gpt-4o")

    client = OpenAI()
    response = client.responses.create(
        model=model,
        tools=[{
            "type": "mcp",
            "server_label": "google_docs",
            "server_url": "http://localhost:9876/mcp",
            "headers": {
                "Authorization": f"Bearer {creds.token}"
            },
            "allowed_tools": [
                "create_doc"
            ]
        }],
        input=PROMPT,
    )

    print(response.output_text)


if __name__ == "__main__":
    main()