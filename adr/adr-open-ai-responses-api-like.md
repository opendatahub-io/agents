# ADR: Risk-adjusted "Open AI Responses API-like" Foundation


## Context

There has been discussion about how to model our approach to agentic functionality and implementation. Two existing precedents are the [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) and the [LlamaStack Agents abstraction](https://llama-stack.readthedocs.io/en/latest/building_applications/agent.html#agent-configuration).

### OpenAI Responses API

This provides an example of agentic-oriented workflows and API design. However, this is a consumer-facing API that exposes many details that might want to be carefully controlled in an enterprise environment. Examples include `parallel_tool_calls` for toggling parallelism of tool calling and `tool_choice` for controlling how tools are chosen whether to be used. Adopting this API wholesale is likely to be in tension with the needs ot an enterprise deployment on top of OpenShift AI.

Consider the perspective of a cluster operator who is deploying a model update. Monitoring, end user chat sessions, agentic state, workflow partial execution all need to persist while surrounding infrastructure is being updated. This suggests that there most likely needs to be an internally managed "agent" abstraction that can be managed by a platform operator. While surely this capability exists internally within OpenAI, it is not exposed in the consumer-facing ResponsesAPI and instead some set of runtime configuration parameters are. In an enterprise API approach, the needs are different, as are requirements around control of runtime configuration parameters.

However, it is important to note that compatibility with existing, widely-adopted APIs such as this one would be a significant advantage for adoption.

### LlamaStack Agents API

This is a server-side abstraction in which agents are explicitly configured, including their available tools. This is no management exposed as REST APIs and it appears that changing agent configuration at runtime is not supported or designed for.

### OpenAI-Like

There is a related precedent of the [`OpenAILike`](https://docs.llamaindex.ai/en/stable/api_reference/llms/openai_like/) abstraction in LlamaIndex that is meant for clients of APIs that largely conform to OpenAI inference APIs but have some differences. For example, this can be used to send requests to a locally running Ollama hosted server. This pattern provides inspiration for the decision here. Especially considering the risk of high rate of change in our approach to AI agents as we learn more about use cases and technical requirements, it provides an example for a risk-adjusted foundation to lay.

## Decision

We will lay a foundation of an "OpenAI Responses API-like" user facing APIs which implements a subset of the OpenAI Responses API.

## Consequences

* We will have to make some decision about what minimal Responses API subset to target at first.
* As we understand more about our domain concepts (agents, tools), we will be able to add new APIs or extend this minimal subset as appropriate.
* We are delaying full modeling of what an agent exactly is for now, though this will not last long.
* We will have to continuously model the agentic domain in order to make informed decisions going forward.
* The risk of over-designing up front is mitigated.
* It will (hopefully) be easier to advocate for REST APIs in LlamaStack when they have a smaller surface area to begin with, which would increase development velocity.