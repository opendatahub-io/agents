# ADR: Adopt Llama Stack Responses API for client-side Agent orchestration

## Context

Red Hat is developing an agentic capability for its AI platforms, including RHEL AI and Red Hat OpenShift AI (RHOAI). The core reasoning engine will leverage the Llama Stack. We are faced with a choice between two available APIs within Llama Stack for implementing agentic logic:

1. **Llama Stack Agents API:** An older API that provides an explicit `Agent` construct on the server. While this simplifies the management of agent definitions for the client, this API is not aligned with the broader AI ecosystem's direction.
2. **Llama Stack Responses API:** A newer API designed for compatibility with the OpenAI Responses API format. This API accepts a list of tools and a chat history and returns a model-generated response, which may include one or more tool calls. It does not provide a server-side `Agent` construct, requiring the client to manage the agent abstraction (tools, workflows, etc.).

The strategic direction from the Llama Stack team is to prioritize the Responses API to maximize compatibility with the vast ecosystem of tools, SDKs, and developer knowledge built around the OpenAI API standard. The older Agents API could be deprecated, heavily refactored, or receive minimal future investment, posing a significant long-term risk.

The core architectural question is: How can we build a robust, developer-friendly agentic framework on an API that does not provide an explicit `Agent` construct without sacrificing the usability that such a construct provides?

One issue that is *not* in scope for this document and is not affected by this decision is whether tools will be invoked by the server or by the client.  For both APIs, it is the case that:

* MCP tools are invoked by the server.  The Responses API can be configured to get approval from the client before invoking the tool, but with either configuration, the tool is invoked by the server.
* "Hosted" or "built-in" tools are also invoked by the server.
* "Function" tools are invoked by the client.

So security and network access concerns for tool calling are outside of the scope of this document because they are the same concerns regardless of which API is used.

## Decision

We will adopt the OpenAI-compatible **Llama Stack Responses API** as the exclusive server interface for agentic reasoning within Red Hat's AI products.

To address the absence of a server-side agent construct, we will need **a client-side Agent construct**.  To address the absence of a server-side agent construct, we will need **a client-side Agent construct**.  The decision about its form is addressed in [ADR: Adopt a Minimal SDK and Ecosystem Strategy for Agents](https://github.com/opendatahub-io/agents/pull/2). Some proposals include adding the functionality to the official Llama Stack client library, creating a new SDK maintained by Red Hat (perhaps as part of OpenDataHub), providing a container image with a simple HTTP API, and adopting a pre-existing SDK such as LangChain. That ADR will cover the pros and cons of these options and propose a final resolution.

## Status

Proposed

## Consequences

### Positive

* **Strategic Alignment & Future-Proofing:** By building on the OpenAI-compatible Responses API, we align with the industry standard and the strategic direction of Llama Stack. This de-risks our platform from the likely deprecation of the older Agents API.
* **Ecosystem Compatibility:** Our agentic capability will be natively compatible with the vast ecosystem of tools, libraries, and monitoring solutions that are built to interface with the OpenAI API format. This accelerates both internal development and customer adoption.
* **Enhanced Flexibility and Control:** A client-side agent construct gives the application developer full control over the agent's execution loop and tool selection. This is critical for complex, mission-critical applications where logic cannot be a black box on a server.
* **Clear Separation of Concerns:** The Llama Stack server is responsible for what it does best: executing LLM inference with tool-calling capabilities. The client is responsible for the application-level concern of orchestrating the agentic logic. This is a clean and scalable architectural pattern.

### Negative

* **Implementation/Support Overhead:** We assume the responsibility for implementing/supporting whatever client-side Agent construct emerges from [ADR: Adopt a Minimal SDK and Ecosystem Strategy for Agents](https://github.com/opendatahub-io/agents/pull/2).
* **Increased Client-side Complexity:** The logic for managing the agent's definition and execution loop now resides on the client. While our chosen Agent construct will abstract this away, the fundamental complexity is shifted from the Llama Stack server to the client. We must ensure our chosen solution is robust, performant, and easy to use. Clients must handle security, availability, and failure recovery, which becomes harder when the client owns the agent definition.  Some clients will be deployed as servers that require auto-scaling and lifecycle management.  Managing the agent object client-side can encourage this “client-as-server” pattern so multiple end-users can share the same agent, further complicating the overall architecture.
* **Difficulty in Sharing and Collaboration:** A server-side agent can be exposed as a persistent, shareable endpoint. A client-side agent, however, exists only within the context of the application that instantiated it. To "share" an agent, one must serialize its configuration, transfer it, and have the recipient re-instantiate a new agent from that data. This "snapshot-and-restore" process creates friction for use cases requiring pre-configured, easily shareable bots or live collaborative agents. (Note: The containerized API proposal could mitigate this, which will be analyzed in the next ADR).
