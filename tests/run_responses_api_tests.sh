#!/usr/bin/env bash

set -euo pipefail

# Configuration
WORK_DIR="/tmp/llama-stack"
LLAMA_STACK_REPO="${LLAMA_STACK_REPO:-https://github.com/meta-llama/llama-stack.git}"
LLAMA_STACK_BRANCH="${LLAMA_STACK_BRANCH:-main}"
LLAMA_STACK_BASE_URL="${LLAMA_STACK_BASE_URL:-http://127.0.0.1:8321}"
RESPONSES_TEST_DIR="tests/integration/responses"

echo "=== Responses API Test Setup ==="
echo "Repository: $LLAMA_STACK_REPO"
echo "Branch: $LLAMA_STACK_BRANCH"
echo "Llama Stack URL: $LLAMA_STACK_BASE_URL"
echo

# Verify llama-stack is accessible
echo "Verifying llama-stack server..."
for i in {1..30}; do
    if curl -fsS "$LLAMA_STACK_BASE_URL/v1/health" > /dev/null 2>&1; then
        echo "✓ Llama Stack server is accessible"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Error: Llama Stack server not accessible at $LLAMA_STACK_BASE_URL"
        exit 1
    fi
    sleep 1
done

# Clone or update llama-stack repository
if [ -d "$WORK_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "$WORK_DIR"
    git fetch origin
    git checkout "$LLAMA_STACK_BRANCH"
    git pull origin "$LLAMA_STACK_BRANCH"
else
    echo "Cloning repository..."
    rm -rf "$WORK_DIR"
    git clone --branch "$LLAMA_STACK_BRANCH" "$LLAMA_STACK_REPO" "$WORK_DIR"
    cd "$WORK_DIR"
fi

# Verify test directory exists
if [ ! -d "$RESPONSES_TEST_DIR" ]; then
    echo "✗ Error: Test directory not found at $RESPONSES_TEST_DIR"
    echo "Searching for test files..."
    find . -type f -name "test*.py" -path "*/responses/*" 2>/dev/null | head -10
    exit 1
fi

# Set environment variables for tests
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Install llama-stack with test dependencies
echo "Installing llama-stack with test dependencies..."
if command -v uv &> /dev/null; then
    # Create and use a venv for the tests
    uv venv .venv
    source .venv/bin/activate
    uv pip install -e ".[client]"
    uv pip install pytest pytest-asyncio python-dotenv
else
    pip install -e ".[dev,client]"
    pip install pytest
fi

# Query available models from the server
echo
echo "=== Querying Available Models ==="
AVAILABLE_MODELS=$(curl -s "$LLAMA_STACK_BASE_URL/v1/models" | python -c "import sys, json; models = json.load(sys.stdin); print('\n'.join([m['id'] for m in models.get('data', [])]))" 2>/dev/null || echo "")

if [ -n "$AVAILABLE_MODELS" ]; then
    echo "Available models on server:"
    echo "$AVAILABLE_MODELS"

    # Find the first LLM model (not embedding)
    TEXT_MODEL=$(echo "$AVAILABLE_MODELS" | grep -v -i "embedding" | head -1)

    # Find embedding model
    EMBED_MODEL=$(echo "$AVAILABLE_MODELS" | grep -i "embedding" | head -1)

    echo
    echo "Selected for testing:"
    echo "  Text model: ${TEXT_MODEL:-<none found>}"
    echo "  Embedding model: ${EMBED_MODEL:-<none found>}"
else
    echo "Could not query models from server, using defaults"
    TEXT_MODEL="${VLLM_INFERENCE_MODEL:-openai/gpt-oss-20b}"
    EMBED_MODEL="${EMBEDDING_MODEL:-sentence-transformers/ibm-granite/granite-embedding-125m-english}"
fi

# Run pytest with proper configuration
echo
echo "=== Running Responses API Tests ==="
echo "Test directory: $RESPONSES_TEST_DIR"
echo "Stack URL: $LLAMA_STACK_BASE_URL"
echo

# Run tests in LIVE mode (actually call the API, don't use recordings)
# Configure the stack to point to our running server
if [ -n "$TEXT_MODEL" ]; then
    python -m pytest -v -s \
        --stack-config="$LLAMA_STACK_BASE_URL" \
        --text-model="$TEXT_MODEL" \
        --embedding-model="$EMBED_MODEL" \
        --inference-mode=live \
        "$RESPONSES_TEST_DIR"
else
    echo "✗ Error: No text model found on server"
    exit 1
fi

echo
echo "✓ Tests completed successfully!"
