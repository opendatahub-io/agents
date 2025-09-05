#! /bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
  echo "Error: No virtual environment found. Please activate a python 3.12 uv virtual environment."
  exit 1
fi

export LLAMA_STACK_LOGGING=all=debug

uv sync
llama stack run --image-type venv run.yaml
