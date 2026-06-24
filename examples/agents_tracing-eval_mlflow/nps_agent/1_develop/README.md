# Develop

This tutorial will walk you through the agent development process with MLflow.

In this tutorial, you'll learn how to:

- Add tracing to Python functions using the `@mlflow.trace` decorator 
- Enable autologging to fully instrument an OpenAI Agent
- Perform evaluations on an agent and review the results
- Share evaluation results with expert reviewers for feedback

## Prerequisites

Complete the [Quick Start](../readme.md#quick-start) setup before running these tutorials.

You will also need:
- Access to an OpenAI-compatible endpoint from your local machine, e.g. OpenAI, vLLM, llama.cpp, Ollama, etc.
- Space on your device to run a local MLflow server (~5 MB)
- Access to a RHOAI cluster with MLflow enabled

## Structure

1. [**Trace**](./1_trace.ipynb): Add tracing to python functions and enable autologging
2. [**Evaluate**](./2_evaluate.ipynb): Perform evaluations on an agent and share results with expert reviewers for feedback

You are encouraged to follow these tutorials in order, but each one does stand on its own if you are only looking to learn more about a specific topic.

## Goals

- The viewer learns how to install MLflow and access the UI running locally.
- The viewer learns how to instrument their agent for MLflow using any of the following:
  - Auto logging via the MLflow tracing SDK
  - Manually logging specific events via the MLflow tracing SDK
  - Manually logging specific events via the OTEL SDK(and the user has some sense of the pros and cons of these three options)
- The viewer learns how to set up an AaaJ with either a generic AaaJ prompt or a specific one designed for their agent.
- The viewer learns how to run an experiment locally ("inner loop eval") using one of those AaaJ's.
- The viewer learns how to navigate the MLflow UI, find the traces for an experiment, and view the results of the AaaJ. They see enough of the results to understand why an AaaJ is useful and what kind of insights they might get about their agent from this technology.