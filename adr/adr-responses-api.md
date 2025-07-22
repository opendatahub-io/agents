# ADR-001: Adopt Llama Stack Responses API for client-side Agent orchestration

**Date:** 2025-07-20

**Status:** Proposed

## 1. Context

Red Hat is developing an agentic capability for its AI platforms, including RHEL AI and Red Hat OpenShift AI (RHOAI). The core reasoning engine will leverage the Llama Stack. We are faced with a choice between two available APIs within Llama Stack for implementing agentic logic:

1. **Llama Stack Agents API:** An older API that provides an explicit, stateful `Agent` construct on the server. The server manages the agent's state and conversation history within a `session`. While this simplifies state management for the client, this API is not aligned with the broader AI ecosystem's direction.
2. **Llama Stack Responses API:** A newer, stateless API designed for compatibility with the OpenAI Responses API format. This API accepts a list of tools and a chat history and returns a model-generated response, which may include one or more tool calls. It does not provide a server-side `Agent` or `session` construct, requiring the client to manage the state of the interaction.

The strategic direction from the Llama Stack team is to prioritize the Responses API to maximize compatibility with the vast ecosystem of tools, SDKs, and developer knowledge built around the OpenAI API standard. The older Agents API could be deprecated, heavily refactored, or receive minimal future investment, posing a significant long-term risk.

The core architectural question is: How can we build a robust, developer-friendly agentic framework on a stateless API without sacrificing the usability that an explicit `Agent` construct provides?

## 2. Decision

We will adopt the **Llama Stack Responses API** as the exclusive backend interface for agentic reasoning within Red Hat's AI products.

To address the absence of a server-side agent object, we will **design and implement a client-side Agent construct**. This client-side agent construct will be responsible for:

* **State Management:** Maintaining the conversation history (user messages, AI responses, tool outputs).
* **Agentic Loop:** Orchestrating the turn-by-turn interaction with the Llama Stack Responses API. This involves:
    1. Formatting the current state (chat history, available tools) into a request.
    2. Sending the request to the API endpoint.
    3. Parsing the API response to distinguish between textual replies and tool call requests.
    4. Executing any requested tool calls using client-side or remote tooling.
    5. Formatting the tool execution results.
    6. Appending the tool results to the history and repeating the loop until a final answer is generated or a stop condition is met.
* **Tool Dispatching:** Managing the registration and invocation of available tools on the client side.

The decision of what form this client-side Agent construct will take will be addressed in a subsequent ADR. Some proposals include adding the functionality to the official Llama Stack client library, creating a new SDK maintained by Red Hat (perhaps as part of OpenDataHub), providing a container image with a simple HTTP API, and adopting a pre-existing SDK such as LangChain. That ADR will cover the pros and cons of these options and propose a final resolution.

## 3. Consequences

### Positive

* **Strategic Alignment & Future-Proofing:** By building on the OpenAI-compatible Responses API, we align with the industry standard and the strategic direction of Llama Stack. This de-risks our platform from the likely deprecation of the older Agents API.
* **Ecosystem Compatibility:** Our agentic capability will be natively compatible with the vast ecosystem of tools, libraries, and monitoring solutions that are built to interface with the OpenAI API format. This accelerates both internal development and customer adoption.
* **Enhanced Flexibility and Control:** A client-side agent construct gives the application developer full control over the agent's execution loop, state, and tool implementation. This is critical for complex, mission-critical applications where logic cannot be a black box on a server.
* **Clear Separation of Concerns:** The Llama Stack server is responsible for what it does best: executing LLM inference with tool-calling capabilities. The client is responsible for the application-level concern of orchestrating the agentic logic. This is a clean and scalable architectural pattern.
* **Stateless Backend:** A stateless API is inherently more scalable, resilient, and easier to manage from an operations perspective. It eliminates concerns about server-side session memory, replication, and expiry.

### Negative

* **Implementation Overhead:** We assume the responsibility for implementing or integrating the client-side Agent construct. This requires dedicated engineering resources, whether for building, testing, or vetting and supporting a third-party solution.
* **Increased Client-side Complexity:** The logic for managing the agent's state and execution loop now resides on the client. While our chosen Agent construct will abstract this away, the fundamental complexity is shifted from the Llama Stack server to the client. We must ensure our chosen solution is robust, performant, and easy to use.
* **Difficulty in Sharing and Collaboration:** A server-side agent can be exposed as a persistent, shareable endpoint. A client-side agent, however, exists only within the context of the application that instantiated it. To "share" an agent, one must serialize its configuration and state, transfer it, and have the recipient re-instantiate a new agent from that data. This "snapshot-and-restore" process creates friction for use cases requiring pre-configured, easily shareable bots or live collaborative agents. (Note: The containerized API proposal could mitigate this, which will be analyzed in the next ADR).
* **Potential for State Inconsistency:** As the client is the source of truth for the agent's state, developers using our solution must correctly manage this state. The design of our chosen Agent construct should provide strong guardrails to prevent common errors.
* **Deferred Decision:** The critical decision on the form and implementation of the Agent construct must be resolved in a timely manner to avoid development bottlenecks.
