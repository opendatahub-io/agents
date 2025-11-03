import logging
import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Global variables copied from app.py
API_KEY = os.getenv("OPENAI_API_KEY", "not applicable")
INFERENCE_SERVER_OPENAI = os.getenv("LLAMA_STACK_SERVER_OPENAI", "http://localhost:8321/v1/openai/v1")
INFERENCE_MODEL = os.getenv("INFERENCE_MODEL", "ollama/llama3.2:3b")

llm = init_chat_model(
    INFERENCE_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=INFERENCE_SERVER_OPENAI,
    use_responses_api=True
)

def testLangChainGuardrails():
    from langchain.agents import create_agent
    from langchain.agents.middleware import PIIMiddleware

    try:
        agent = create_agent(
            # model="ollama:llama-guard3:8b",
            model=llm,
            middleware=[
                # Redact emails in user input before sending to model
                PIIMiddleware(
                    "email",
                    strategy="redact",
                    apply_to_input=True,
                ),
                # Mask credit cards in user input
                PIIMiddleware(
                    "credit_card",
                    strategy="mask",
                    apply_to_input=True,
                ),
                # Block API keys - raise error if detected
                PIIMiddleware(
                    "api_key",
                    detector=r"sk-[a-zA-Z0-9]{32}",
                    strategy="block",
                    apply_to_input=True,
                ),
            ],
        )

        logger.info("testLangChainGuardrails calling invoke")

        # When user provides PII, it will be handled according to the strategy
        result = agent.invoke({
            "messages": [{"role": "user", "content": "My email is john.doe@example.com and card is 4532-1234-5678-9010"}]
        })
        logger.info("testLangChainGuardrails returned")

        print(result)
    except Exception as e:
        logger.info(f"testLangChainGuardrails failed with error: '{e}'")

if __name__ == '__main__':
    testLangChainGuardrails()
