import logging
import os
import asyncio
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
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

# Global variables for MCP tools
mcp_tools = None
llm_with_mcp_tools = None

# testLangChainMcp is not part of the customer service sample based on langchain/langgraph and the llama stack responses
# api per se ... just put it in here to vet various llama stack version / model combinations

# see debug-notes-during-mcp-testing.txt for details

async def testLangChainMcp():
    global mcp_tools, llm_with_mcp_tools

    mcp_client = MultiServerMCPClient(
        {
            "kubernetes": {
                # make sure you start your kubernetes mcp server on port 8080
                "url": "http://localhost:8080/mcp",
                "transport": "streamable_http",
            }
        }

    )
    mcp_tools = await mcp_client.get_tools()
    # reduce the tool list to just 'namespaces_list'
    mcp_tools = [tool for tool in mcp_tools if tool.name == 'namespaces_list']
    llm_with_mcp_tools = llm.bind_tools(mcp_tools)
    logger.info("testLangChainMcp calling tools invoke")
    try:
        mcp_resp = await llm_with_mcp_tools.ainvoke("using the supplied kubernetes tool, call the tool that lists all the namespaces in the kubernetes cluster")
        logger.info("testLangChainMcp calling tools returned")
        print(mcp_resp)
    except Exception as e:
        logger.info(f"testLangChainMcp failed with error: '{e}'")

if __name__ == '__main__':
    asyncio.run(testLangChainMcp())
