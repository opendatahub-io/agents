#!/bin/bash
# Entry point — packages and serves the agent via MLflow
# The agent spawns the MCP server via stdio on each request
# Traces go to MLFLOW_TRACKING_URI (RHOAI or local)

set -e

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
PYTHON="${PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

export MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME:-nps-agent}"

# Package npsagent.py into a temp dir (instant, no network)
MODEL_DIR=$(mktemp -d)

$PYTHON -c "
import mlflow
mlflow.pyfunc.save_model(python_model='npsagent.py', path='$MODEL_DIR')
"

echo "Traces:    ${MLFLOW_TRACKING_URI:-(not set)}"
echo "Listening: http://$HOST:$PORT"

exec $PYTHON "${MODEL_DIR}/npsagent.py" --host "$HOST" --port "$PORT"
