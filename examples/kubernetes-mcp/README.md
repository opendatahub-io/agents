# Kubernetes MCP example

This is an example of making an MCP tool call against the kubernetes-mcp-server from [kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) over SSE.
This server supports authentication via bearer tokens at the very least, which is what this example will demonstrate.

*NOTE:* This workflow is built using llama stack + responses API + a local vLLM instance serving `Qwen/Qwen3-0.6B` model for tool calling. As such, instructions are included to get these individual pieces set up, but there are also variations of this setup which are not covered in this README (such as substituing vLLM for an OpenAI call instead).

## Pre-requisites

### Kubernetes cluster

It is fairly straightforward to get a container based kubernetes cluster deployed locally using something like [kind](https://github.com/kubernetes-sigs/kind) or [Minikube](https://github.com/kubernetes/minikube).
Those using Podman on MacOS can look at [this guide](https://github.com/southsidedean/deploy-kind-using-podman-macos) to have kind deployed on top of it.

Once the cluster is deployed, apply the included `demo.yaml` file against the cluster.

```shell
kubectl apply -f demo.yaml
```

This will create the following resources:

- A new namespace `demo-auth`
- A pod in that namespace
- A serviceaccount
- A Role allowing the serviceaccount to only list pods in that namespace
- A Rolebinding for that serviceaccount

#### Extracting the serviceaccount token

Retrieve the serviceaccount token by running the following command:

```shell
kubectl -n demo-auth create token sa-pod-reader
```

Export the token to `KUBE_TOKEN` in your shell environemnt.

### Kubernetes-mcp-server

Clone the project [kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) locally and ensure you have `uv` installed.

Execute the following command to get the server running:
`uvx kubernetes-mcp-server --port 8080`

You should see the following output:

```shell
Installed 1 package in 2ms
Downloading kubernetes-mcp-server-darwin-arm64 from https://github.com/containers/kubernetes-mcp-server/releases/download/v0.0.50/kubernetes-mcp-server-darwin-arm64
I0915 08:00:42.389742   23670 http.go:57] "Streaming and SSE HTTP servers starting on port 8080 and paths /mcp, /sse, /message"
```

Optionally, run the mcp inspector in a separate terminal to verify that the mcp server is able to communicate with the kubernetes server correctly and execute all the avaialble tools.

```shell
make build
npx @modelcontextprotocol/inspector@latest $(pwd)/kubernetes-mcp-server
```

You should see the following output:

```shell
Starting MCP inspector...
⚙️ Proxy server listening on localhost:6277
🔑 Session token:<token>
   Use this token to authenticate requests or set DANGEROUSLY_OMIT_AUTH=true to disable auth

🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>

🌐 Opening browser...
New SSE connection request. NOTE: The SSE transport is deprecated and has been replaced by StreamableHttp
```

### vLLM

Ensure that you have a local python environment with vLLM installed in it. This workflow was done using vLLM `v0.10.1.1`.
Run the following command to get vLLM running:

```shell
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen3-0.6B --port 8000 --enable-auto-tool-choice --tool-call-parser hermes --tensor-parallel-size 4
```

*NOTE:*

- This command prescribes the `hermes` tool call parser since this works well with the Qwen3-0.6B model. Update this with the appropriate parser if using a different model.
- Update `tensor-parallel-size` value depending on how many GPUs you have available on your system.

If running vLLM on a remote instance, make sure to perform port forwarding to port 8000 on your local machine as this workflow assumes vLLM is available at localhost:8000.

### LLama Stack

Ensure that llama stack is installed in your local python environment, and that the included `run.yaml` is populated with the right details (specifically the model-id and vllm URL).

Start the llama stack server by running the command:

```shell
llama stack run run.yaml --image-type venv
```

## Running an agentic query

export the URL for your inference server (llama stack in this case):

```shell
export OPENAI_BASE_URL=http://localhost:8321/v1/openai/v1
```

### Go client

Run Go mod tidy

```shell
go mod tidy
```

Run the demo script

```shell
go run client.go
```

### Python client

Run the python script

```shell
python client.py
```

## Expected Output

The included `client.go` script includes 2 queries that users can run by uncommenting the appropriate one.

Query 1: "Using the tool provided, list all pods in the demo-auth namespace"

This is expected to succeed since the token we have passed in should have privileges to list all the pods in this namespace.

Expected output:

```shell
2025/09/15 08:46:14 Using model Qwen/Qwen3-0.6B
2025/09/15 08:46:17 <think>
Okay, the user wants to list all pods in the demo-auth namespace. I remember that the tool available is pods_list_in_namespace. The parameters required are the namespace. The user specified "demo-auth", so I should call that function with the namespace set to "demo-auth". The response provided in the tool response shows the pods in that namespace. I need to present this information clearly to the user. Let me check if there's anything else they might need, but since the response is already given, I'll format it as a simple answer.
</think>

Here are all pods in the `demo-auth` namespace:

- **`pod-reader-test`** - Running (1/1)
  IP: `10.244.0.5`
  Node: `kind-control-plane`

Let me know if you'd like further details!
```

Query 2: "Using the tool provided, list all pods in the kube-system namespace"

This is expected to fail since the token we supplied should not have privileges to list pods in any namespace other than `demo-auth`.

Expected output:

```shell
2025/09/15 08:47:37 Using model Qwen/Qwen3-0.6B
2025/09/15 08:47:41 <think>
Okay, the user is trying to list all pods in the kube-system namespace, but there's a permission error. Let me check the error message again. The error says "pods is forbidden: User 'system:serviceaccount:demo-auth:sa-pod-reader' cannot list resource 'pods' in API group '' in the namespace 'kube-system'".

Hmm, the problem here is that the user's current user context might not have the necessary permissions. The error message mentions a specific user and a namespace, so the issue is likely related to the user's role or permissions. The user might be trying to list pods but their cluster role doesn't allow access to the pods resource.

I need to figure out how to handle this. Since the user is using the tool, maybe they need to adjust their permissions. The error suggests that the user is part of the service account 'demo-auth:sa-pod-reader', which is allowed to list pods, but perhaps the actual access is blocked. Alternatively, maybe the user is trying to list pods from a different namespace, but the error is pointing to the kube-system namespace.

Wait, the function call was made with "pods_list_in_namespace" and the namespace set to "kube-system". The tool response says it failed because of the permission. So the solution would be to check if the user has the correct permissions. Maybe they need to modify their role or ensure they are using the right namespace. But since the user is using the tool, perhaps they should verify their cluster roles. Alternatively, maybe there's a misconfiguration in the cluster settings.

Wait, the error message mentions the API group "" which might be a placeholder. Maybe the user is trying to list pods in a non-existent API group, but that's unlikely. The key point is that the user's current permissions are blocked. So the next step would be to inform them about the permission issue and suggest adjusting their cluster role or checking their access. But since the user is using the tool, they might need to adjust their permissions before proceeding. Alternatively, maybe there's a way to list pods without that restriction, but I'm not sure. The user's question is to list pods in the kube-system namespace, so the answer should address the permission error and provide a solution.
</think>

The error indicates that the user's cluster role does not allow listing pods in the `kube-system` namespace. To resolve this, ensure that the user has the appropriate cluster roles or that the namespace is correctly configured. If the issue persists, check the cluster's access policies or verify that the user is part of the correct service account.
```
