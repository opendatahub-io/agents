# Validate File Search (RAG) with GPT-OSS via Responses API

## Objective

Manually test that GPT-OSS models can correctly perform RAG operations (file-search) through the Llama Stack Responses API. Test both models (20b, 120b) with the main branch of vLLM.

## Test Results (02/03/2026)

⚠️ **GPT-OSS-120b** partially performs file search (RAG) operations via vLLM 0.11.2+rhai5 (see Prompt 2 issue below).
✅ **GPT-OSS-20b** successfully performs file search (RAG) operations via vLLM 0.11.2+rhai5.

## Setup

1. **vLLM**: Running on OpenShift with GPT-OSS models using vLLM 0.11.2+rhai5
2. **Llama Stack**: Configured with:
   - `sentence-transformers` provider for embeddings
   - `all-MiniLM-L6-v2` embedding model (384 dimensions)
   - `faiss` vector store provider
   - `meta-reference` agent provider
3. **Vector Store**: Automatically created by notebooks if not provided via `VECTOR_STORE_IDS` environment variable
4. **Reference Document**: `reference.txt` containing test data about Silas Vance and team

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

**Response:** The uploaded material contains a single text file (reference.txt) that provides the following details:
- **Person:** Silas Vance – an Arcturus Systems Engineer  
- **Team:** Works in the Nexus and NCP team  
- **Current work:** Manually testing modular‑stack tools with open‑source models on a high‑performance inference engine  
- **Manager:** Alaric  
- **Teammates:** Bastien, Jace, Elian, Amara, Kaelen, Merrick, Seraphina, Garek, Nolan, and Rina  
- **Planned project:** Merrick and Silas intend to build a Test Strategy and Test Automation framework for the modular‑stack responses API

### Prompt 2
**Status:** completed | **File search:** False | **Tool calls:** 0 | **Messages:** 1

**Response:** I'm happy to help, but I don't see any documents attached to this conversation. Could you please upload the files you'd like me to search and summarize, or let me know which specific documents you're referring to? Once I have them, I'll review the content and provide a concise summary of the key points.

⚠️ **Issue:** The model did not invoke the `file_search` tool for this prompt. The prompt "Search the uploaded documents and summarize the key points" does not explicitly mention "file search" or "tool", and the 120b model requires explicit tool instructions to invoke tools. See "Model Behavior Differences" section below.

### Prompt 3
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded documents primarily discuss the work of Silas Vance and the Nexus & NCP team at Arcturus, focusing on manually testing modular‑stack tools with open‑source models on a high‑performance inference engine...

## GPT-OSS-20b Results

### Prompt 1
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded documents contain information about a person named Silas Vance, an Arcturus Systems Engineer who works in the Nexus and NCP team. It describes his current work on manually testing modular stack tools with open‑source models on a high‑performance inference engine. The manager of Silas Vance is Alaric, and his teammates include Bastien, Jace, Elian, Amara, Kaelen, Merrick, Seraphina, Garek, Nolan, and Rina. Additionally, it mentions that Merrick and Silas are planning to build a Test Strategy and Test Automation framework for the modular‑stack responses API.

### Prompt 2
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** - Silas Vance is an Arcturus Systems Engineer working with the Nexus and NCP team, focusing on manually testing modular‑stack tools that run on open‑source models using a high‑performance inference engine.  
- His manager is Alaric, and his teammates include Bastien, Jace, Elian, Amara, Kaelen, Merrick, Seraphina, Garek, Nolan, and Rina.  
- Merrick and Silas are planning to build a Test Strategy and Test Automation framework for the modular‑stack responses API.

### Prompt 3
**Status:** completed | **File search:** True | **Tool calls:** 1 | **Messages:** 1

**Response:** The uploaded documents discuss Arcturus Systems Engineering, the Nexus and NCP team, manual testing of modular stack tools with open‑source models on a high‑performance inference engine, and plans for building a Test Strategy and Test Automation framework for the modular‑stack responses API...

## Analysis

**GPT-OSS-20b successfully performs file search (RAG) operations through Llama Stack Responses API** using vLLM 0.11.2+rhai5:

- ✅ Correctly invokes `file_search` tool with vector store IDs for all prompts
- ✅ Retrieves relevant document chunks from the vector store
- ✅ Generates accurate responses based on retrieved context
- ✅ Includes file citations in responses
- ✅ All three test prompts completed successfully with accurate information retrieval

**GPT-OSS-120b partially performs file search (RAG) operations:**

- ✅ Correctly invokes `file_search` tool when explicitly instructed (Prompts 1 and 3)
- ⚠️ Does not invoke `file_search` tool when prompt lacks explicit tool instructions (Prompt 2)
- ✅ Retrieves relevant document chunks when tool is invoked
- ✅ Generates accurate responses based on retrieved context
- ✅ Includes file citations in responses when tool is used

**Key Observations:**
- File search tool is properly triggered for all prompts in 20b model
- File search tool is triggered for 2 out of 3 prompts in 120b model (see Model Behavior Differences below)
- Retrieved content matches the reference document accurately when tool is used
- Both models correctly reference "uploaded documents" in responses when tool is invoked
- Response quality is high with proper summarization and topic extraction
- All key facts from the reference document (Silas Vance, Arcturus Systems Engineer, Nexus and NCP team, manager Alaric, teammates, and test automation framework plans) are accurately retrieved and presented when tool is used

**Model Behavior Differences:**

The 120b model requires **explicit tool instructions** to invoke the `file_search` tool, while the 20b model can **infer tool usage** from context:

- **Prompt 1**: "Use the file search tool..." → Both models use tool ✅
- **Prompt 2**: "Search the uploaded documents..." → 20b uses tool ✅, 120b does not ⚠️
- **Prompt 3**: "Use file search to find..." → Both models use tool ✅

**Root Cause**: The 120b model is stricter about tool invocation and only uses tools when explicitly instructed. Prompt 2 does not contain the words "file search" or "tool", so the 120b model responded directly without invoking the tool, while the 20b model inferred that "search the uploaded documents" requires the file_search tool.

**Recommendation**: For consistent behavior across both models, prompts should explicitly mention "file search" or "file search tool" when tool usage is required.

## Differences from Web Search

Unlike web search which queries external APIs (Brave Search, Tavily), file search requires:
- **Vector Store**: Database for storing document embeddings
- **Embedding Model**: Converts text to vectors (e.g., `sentence-transformers/all-MiniLM-L6-v2`)
- **File Processing**: Documents must be uploaded, chunked, and embedded before search

The notebooks handle vector store creation automatically for new users.
