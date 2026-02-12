#!/usr/bin/env bash

set -euo pipefail

# Configuration
WORK_DIR="/tmp/opendatahub-tests"
OPENDATAHUB_TESTS_REPO="${OPENDATAHUB_TESTS_REPO:-https://github.com/opendatahub-io/opendatahub-tests.git}"
OPENDATAHUB_TESTS_BRANCH="${OPENDATAHUB_TESTS_BRANCH:-main}"
LLAMA_STACK_BASE_URL="${LLAMA_STACK_BASE_URL:-http://127.0.0.1:8321}"
RESPONSES_TEST_DIR="tests/llama_stack/responses"

echo "=== Responses API Test Setup ==="
echo "Repository: $OPENDATAHUB_TESTS_REPO"
echo "Branch: $OPENDATAHUB_TESTS_BRANCH"
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

# Clone or update opendatahub-tests repository
if [ -d "$WORK_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "$WORK_DIR"
    git fetch origin
    git checkout "$OPENDATAHUB_TESTS_BRANCH"
    git pull origin "$OPENDATAHUB_TESTS_BRANCH"
else
    echo "Cloning repository..."
    rm -rf "$WORK_DIR"
    git clone --branch "$OPENDATAHUB_TESTS_BRANCH" "$OPENDATAHUB_TESTS_REPO" "$WORK_DIR"
    cd "$WORK_DIR"
fi

# Verify test directory exists
if [ ! -d "$RESPONSES_TEST_DIR" ]; then
    echo "✗ Error: Test directory not found at $RESPONSES_TEST_DIR"
    ls -la tests/llama_stack/ 2>/dev/null || echo "tests/llama_stack directory not found"
    exit 1
fi

# Set environment variables for tests
export LLAMA_STACK_BASE_URL="$LLAMA_STACK_BASE_URL"
export LLAMA_STACK_URL="$LLAMA_STACK_BASE_URL"
export KUBECONFIG=""
export SKIP_K8S_SETUP="true"
export OCP_RESOURCES_SKIP="true"
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Install test dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv pip install -r requirements.txt
    else
        pip install -r requirements.txt
    fi
fi

# Run pytest
echo
echo "=== Running Responses API Tests ==="
if command -v uv &> /dev/null; then
    uv run python -m pytest -v "$RESPONSES_TEST_DIR"
else
    python -m pytest -v "$RESPONSES_TEST_DIR"
fi

echo
echo "✓ Tests completed successfully!"
