import logging

from flask import Flask, request, send_from_directory
from langchain.chat_models import init_chat_model
from openai import OpenAI
import os
from dotenv import load_dotenv
import asyncio
import threading
import uuid
from workflow import make_workflow, submission_states

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY=os.getenv("OPENAI_API_KEY", "not applicable")
INFERENCE_SERVER_OPENAI = os.getenv("LLAMA_STACK_SERVER_OPENAI", "http://localhost:8321/v1/openai/v1")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "ollama/llama3.2:3b")
GUARDRAIL_MODEL = os.getenv("GUARDRAIL_MODEL", "llama-guard3:8b")
MCP_TOOL_MODEL = os.getenv("MCP_TOOL_MODEL", "ollama/llama3.2:3b")
GIT_TOKEN = os.getenv("GIT_TOKEN", "not applicable")
GITHUB_URL=os.getenv("GITHUB_URL", "not applicable")
GITHUB_ID=os.getenv("GITHUB_ID", "not applicable")


llm = init_chat_model(
    INFERENCE_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=INFERENCE_SERVER_OPENAI,
    use_responses_api=True
)

# so the underlying OpenAI SDK client exists off of llm from init_chat_model, via llm.root_client, but it is a
# private attribute; so we open up a separate openai client for moderations
openaiClient = OpenAI(api_key=API_KEY, base_url=INFERENCE_SERVER_OPENAI)

workflow = make_workflow(
    llm,
    openaiClient,
    GUARDRAIL_MODEL,
    MCP_TOOL_MODEL,
    GIT_TOKEN,
    GITHUB_URL,
    GITHUB_ID
)

async def invoke_workflow_async(question, submission_id):
    response = await asyncio.to_thread(workflow.invoke, {"input": question, "submissionID": submission_id})
    return response

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

def run_async_task(question, submission_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(invoke_workflow_async(question, submission_id))
    loop.close()

@app.route('/submit-question', methods=['POST'])
def submit_question():
    question = request.form.get('question')
    if not question:
        return '<html><body><p>Error: No question provided</p></body></html>', 400

    # Generate random submission ID
    submission_id = str(uuid.uuid4())

    # Process the question using your workflow asynchronously
    threading.Thread(target=run_async_task, args=(question, submission_id)).start()
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processing - Question Cart</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            transition: background-color 0.3s, color 0.3s;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #28a745;
            margin-bottom: 20px;
        }}
        .success-section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #d4edda;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}
        .info-section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        .label {{
            font-weight: bold;
            color: #155724;
            margin-bottom: 5px;
        }}
        .info-label {{
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }}
        .content {{
            margin-top: 5px;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        .submission-id {{
            font-family: monospace;
            background-color: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            display: inline-block;
            margin-top: 5px;
            font-size: 14px;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .instructions {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .instructions .label {{
            color: #856404;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #333;
                color: #f0f0f0;
            }}
            .container {{
                background-color: #444;
            }}
            .success-section {{
                background-color: #2d4a2d;
            }}
            .info-section {{
                background-color: #555;
            }}
            .instructions {{
                background-color: #4a4020;
            }}
            .label {{
                color: #90ee90;
            }}
            .info-label {{
                color: #4d9fff;
            }}
            .submission-id {{
                background-color: #555;
                color: #f0f0f0;
            }}
            .instructions .label {{
                color: #ffd966;
            }}
            h1 {{
                color: #90ee90;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Processing Started</h1>
        <div class="success-section">
            <div class="label">Status:</div>
            <div class="content">Your question has been submitted successfully and is being processed.</div>
        </div>
        <div class="info-section">
            <div class="info-label">Submission ID:</div>
            <div class="content">
                <div class="submission-id">{submission_id}</div>
            </div>
        </div>
        <div class="instructions">
            <div class="label">Next Steps:</div>
            <div class="content">
                Go to <a href="http://localhost:5000/get-response">http://localhost:5000/get-response</a> and supply the submissionID above to see the response when it is ready.
                <br><br>
                <strong>Note:</strong> The response may not be ready immediately. Please wait and retry as needed.
            </div>
        </div>
        <p><a href="/">Submit another question</a></p>
    </div>
</body>
</html>'''

@app.route('/get-response', methods=['GET', 'POST'])
def get_response():
    # Handle GET request - show the form
    if request.method == 'GET':
        return send_from_directory('.', 'get-response.html')

    # Handle POST request - process the submission
    submission_id = request.form.get('submissionID')
    if not submission_id:
        return '<html><body><p>Error: No submissionID provided</p></body></html>', 400

    # Look up the response in submission_states
    if submission_id in submission_states:
        submission_state = submission_states[submission_id]
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Response - Question Cart</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            transition: background-color 0.3s, color 0.3s;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #007bff;
            margin-bottom: 20px;
        }}
        .info-section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        .label {{
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }}
        .content {{
            margin-top: 5px;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        .content-scrollable {{
            margin-top: 5px;
            line-height: 1.6;
            white-space: pre;
            overflow-x: auto;
            max-width: 100%;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #333;
                color: #f0f0f0;
            }}
            .container {{
                background-color: #444;
            }}
            .info-section {{
                background-color: #555;
            }}
            h1 {{
                color: #4d9fff;
            }}
            .label {{
                color: #4d9fff;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Response Found</h1>
        <div class="info-section">
            <div class="label">Submission ID:</div>
            <div class="content">{submission_id}</div>
        </div>
        <div class="info-section">
            <div class="label">User Input:</div>
            <div class="content">{submission_state.get('input', 'N/A')}</div>
        </div>
        <div class="info-section">
            <div class="label">Initial Classification:</div>
            <div class="content">{submission_state.get('classification_message', 'N/A')}</div>
        </div>
        <div class="info-section">
            <div class="label">Preliminary Diagnostics:</div>
            <div class="content-scrollable">{submission_state.get('mcp_output', 'N/A')}</div>
        </div>
        <div class="info-section">
            <div class="label">GitHub Tracking Issue:</div>
            <div class="content">{'<a href="' + submission_state.get('github_issue', '') + '" target="_blank">' + submission_state.get('github_issue', '') + '</a>' if submission_state.get('github_issue') else 'N/A'}</div>
        </div>
        <p><a href="/">Submit another question</a></p>
    </div>
</body>
</html>'''
    else:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Question Cart</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            transition: background-color 0.3s, color 0.3s;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #dc3545;
            margin-bottom: 20px;
        }}
        .error-section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8d7da;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
        }}
        .label {{
            font-weight: bold;
            color: #721c24;
            margin-bottom: 5px;
        }}
        .content {{
            margin-top: 5px;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #333;
                color: #f0f0f0;
            }}
            .container {{
                background-color: #444;
            }}
            .error-section {{
                background-color: #5a2a2a;
            }}
            h1 {{
                color: #ff6b6b;
            }}
            .label {{
                color: #ff6b6b;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Error: Response Not Found</h1>
        <div class="error-section">
            <div class="label">Error Message:</div>
            <div class="content">No response found for this submissionID</div>
        </div>
        <div class="error-section">
            <div class="label">Submission ID:</div>
            <div class="content">{submission_id}</div>
        </div>
        <p><a href="/">Return to home</a> | <a href="/get-response">Try another submission ID</a></p>
    </div>
</body>
</html>''', 404

if __name__ == '__main__':
    app.run(debug=True)