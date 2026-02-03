# Validate File Search (RAG) with GPT-OSS via Responses API

## Objective

Manually test that GPT-OSS models can correctly perform RAG operations (file-search) through the Llama Stack Responses API. Test both models (20b, 120b) with the main branch of vLLM.

## Test Results (02/02/2026)

✅ **GPT-OSS-120b** successfully performs file search (RAG) operations via vLLM 0.11.2+rhai5.
✅ **GPT-OSS-20b** successfully performs file search (RAG) operations via vLLM 0.11.2+rhai5.

## Setup

1. **vLLM**: Running on OpenShift with GPT-OSS models using vLLM 0.11.2+rhai5
2. **Llama Stack**: Configured with:
   - `sentence-transformers` provider for embeddings
   - `all-MiniLM-L6-v2` embedding model (384 dimensions)
   - `faiss` vector store provider
   - `meta-reference` agent provider
3. **Vector Store**: Automatically created by notebooks if not provided via `VECTOR_STORE_IDS` environment variable
4. **Reference Document**: `reference.txt` containing test data about Hamid Moghani and team

## Notebooks

| Notebook | Description |
|----------|-------------|
| [GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb](GPT-OSS-20b_with_vLLM_0.11.2+rhai5.ipynb) | Tests GPT-OSS-20b file search (RAG) operations |
| [GPT-OSS-120b_with_vLLM_0.11.2+rhai5.ipynb](GPT-OSS-120b_with_vLLM_0.11.2+rhai5.ipynb) | Tests GPT-OSS-120b file search (RAG) operations |

Each notebook:
- Automatically creates a vector store and uploads `reference.txt` if `VECTOR_STORE_IDS` is not set
- Tests three prompts requiring file search:
  1. "Use the file search tool to find information in the uploaded documents. What information is available?"
  2. "Search the uploaded documents and summarize the key points."
  3. "What are the main topics covered in the uploaded documents? Use file search to find this information."

## GPT-OSS-120b Results

### Prompt 1
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded document contains a short profile of a Red Hat engineer:
- **Name:** Hamid Moghani  
- **Team:** Agentic and MCP  
- **Current work:** Manually testing Llama Stack tools with GPT‑OSS mod...

### Prompt 2
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** **Summary of the uploaded document**
- Hamid Moghani is a Red Hat Engineer who works in the **Agentic and MCP team**.  
- He is currently **manually testing Llama Stack tools** with GPT‑OSS models on...

### Prompt 3
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded document primarily discusses:
- **Hamid Moghani's role** – a Red Hat Engineer in the Agentic and MCP team  
- **Current project focus** – manually testing Llama Stack tools with GPT‑OSS ...

## GPT-OSS-20b Results

### Prompt 1
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded document (reference.txt) contains the following information about Hamid Moghani and his work context:
- He is a Red Hat Engineer who works in the Agentic and MCP team.
- He is currently testing llama stack tools with GPT‑OSS models on vLLM...

### Prompt 2
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** Key points from the uploaded documents:
- Hamid Moghani is a Red Hat Engineer in the Agentic and MCP team.
- He is currently focused on manually testing Llama‑Stack tools that use GPT‑OSS models running on vLLM...

### Prompt 3
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The documents focus on Hamid Moghani's role as a Red Hat engineer on the Agentic and MCP teams, his current work manually testing llama‑stack tools with GPT‑OSS models on vLLM, and his collaboration with Mike to build a test strategy and test‑automation framework...

## Analysis

**Both GPT-OSS-120b and GPT-OSS-20b successfully perform file search (RAG) operations through Llama Stack Responses API** using vLLM 0.11.2+rhai5:

- ✅ Correctly invokes `file_search` tool with vector store IDs
- ✅ Retrieves relevant document chunks from the vector store
- ✅ Generates accurate responses based on retrieved context
- ✅ Includes file citations in responses
- ✅ All three test prompts completed successfully with accurate information retrieval

**Key Observations:**
- File search tool is properly triggered for all prompts in both models
- Retrieved content matches the reference document accurately
- Both models correctly reference "uploaded documents" in responses
- Response quality is high with proper summarization and topic extraction
- All key facts from the reference document (Hamid Moghani, Red Hat Engineer, Agentic and MCP team, manager Justin, teammates, and test automation framework plans) are accurately retrieved and presented

## Differences from Web Search

Unlike web search which queries external APIs (Brave Search, Tavily), file search requires:
- **Vector Store**: Database for storing document embeddings
- **Embedding Model**: Converts text to vectors (e.g., `sentence-transformers/all-MiniLM-L6-v2`)
- **File Processing**: Documents must be uploaded, chunked, and embedded before search

The notebooks handle vector store creation automatically for new users.
