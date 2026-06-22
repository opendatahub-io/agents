# Observe

This tutorial will walk you through the agent observation process with MLflow.

In this tutorial, you'll learn how to:

- Capture traces from a running agent deployed on OpenShift AI into MLflow
- Build evalaution scorers and LLM-judge to evaluate the agent application
- Perform outer loop evaluations on the agent application traces and review the results
- Share evaluation results with expert reviewers for feedback

## Prerequisites

Complete the [Quick Start](../readme.md#quick-start) setup before running these tutorials.

You will also need:
- Access to an OpenAI-compatible LLM endpoint e.g. OpenAI, vLLM, llama.cpp, Ollama, etc.
- Access to an OpenShift AI cluster with MLflow enabled
- A running agent application deployed on OpenShift AI

## Structure

1. [**Evaluate**](./outer_loop_eval.ipynb): Perform outer loop evaluations on the deployed agent application

## Goals

- The viewer learns how to view and capture traces from a deployed agent application in MLflow
- The viewer learns how to set up MLflow's in-built evaluation scorers and LLM-judge for evaluating the agent application
- The viewer learns how to execute an evaluation run using the defined scorers against the agent application traces
- The viewer learns how to navigate the MLflow UI, find the traces for an experiment, and view the results of the evaluation run. Through these results we can understand why evaluation is useful and gain insights about our agent application performance.
