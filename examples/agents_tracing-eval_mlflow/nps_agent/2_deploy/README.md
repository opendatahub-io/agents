# Deploy NPS Agent to RHOAI

This directory contains everything needed to deploy the NPS Agent as an HTTP endpoint on **Red Hat OpenShift AI (RHOAI)** with MLflow tracing.

The agent logic is identical to the [Evaluate notebook](../1_develop/2_evaluate.ipynb) — we just wrap it in an MLflow `ResponsesAgent` for serving.

## Files

| File | Purpose |
|---|---|
| [`deploy.ipynb`](./deploy.ipynb) | Step-by-step deployment notebook |
| [`npsagent.py`](./npsagent.py) | Agent + MLflow `ResponsesAgent` wrapper for HTTP serving |
| [`nps_mcp_server.py`](./nps_mcp_server.py) | FastMCP server exposing NPS API tools (spawned on-demand per request) |
| [`app.sh`](./app.sh) | Container entry point — packages the agent and starts `mlflow models serve` |
| [`requirements.txt`](./requirements.txt) | Python dependencies for the s2i build |
| [`nps-agent.yaml`](./nps-agent.yaml) | OpenShift Template (BuildConfig, Deployment, Service, Route) |
| [`.s2i/environment`](./.s2i/environment) | Tells s2i to use `app.sh` as the startup script |

## Prerequisites

- An OpenShift cluster with RHOAI and MLflow configured ([Cluster Setup Guide](https://docs.google.com/document/d/1ZzuGAY1gSamOLsznwbaL7xFkJ1JjHWpnyjk0tV12YVg/edit?tab=t.0#heading=h.jgt5ddlrwyvc))
- The `oc` CLI installed and logged in
- A `.env` file in the repo root with:
  ```
  OPENAI_API_KEY=...
  OPENAI_BASE_URL=https://api.openai.com/v1
  OPENAI_MODEL_NAME=gpt-4o-mini
  NPS_API_KEY=...
  MLFLOW_TRACKING_URI=https://mlflow-tracking-route-redhat-ods-applications.apps.<cluster>
  ```

## Quick Start

Open [`deploy.ipynb`](./deploy.ipynb) and run through the steps:

1. **Create an OpenShift project** — `oc new-project nps-agent-<yourname>`
2. **Create secrets** — pushes API keys as an OpenShift Secret
3. **Grant service account access** — gives the pod admin access for MLflow auth
4. **Apply the template** — `oc process` creates all resources in one shot
5. **Wait for the build** — s2i clones the repo, installs deps, builds the image
6. **Verify the pod** — check it's `Running`
7. **Get the route URL** — grab the public HTTPS endpoint
8. **Test the agent** — send a question to `POST /invocations`
9. **View traces** — open the MLflow UI to see auto-traced LLM calls and tool invocations

See [`deploy.ipynb`](./deploy.ipynb) for the full walkthrough, architecture details, and rebuild/cleanup instructions.
