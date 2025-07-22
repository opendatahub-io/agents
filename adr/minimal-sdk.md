# ADR: Adopt a Minimal SDK and Ecosystem Strategy for Agents

## Context

Following the decision in [ADR: Adopt Llama Stack Responses API for Agentic MCP](https://github.com/opendatahub-io/agents/pull/1) to adopt the Llama Stack Responses API, we committed to providing a client-side "Agent construct" to manage state and orchestrate the agentic loop. This ADR addresses the critical follow-up question: what specific form will this construct take?

The goal is to provide a solution that enables developers, offers a clear path for simple use cases, and integrates well with the broader AI ecosystem, all while managing Red Hat's engineering investment and long-term strategy.

We considered several options for implementing this agent construct:

1. **Extend Llama Stack Client SDK:** Add the agent logic directly into the official Llama Stack client. This would create a strong, unified story but conflicts with the client's design as a thin, auto-generated layer.
2. **New, Full-Featured Red Hat SDK:** Build a comprehensive, competitive agent framework from the ground up. This offers maximum control but requires a very significant, long-term engineering investment. Also, even if it was done well, it would be difficult to drive adoption due to strong competition in this space.
3. **New, Full-Featured Red Hat Container/Service:** The same as above, but delivered as a containerized HTTP service. This could simplify agent sharing and support a broader assortment of programming languages, but it adds operational complexity for developers.
4. **Adopt a Single Third-Party SDK:** Formally adopt, package, and recommend a single existing framework (e.g., LangChain) as the "official" way to build agents on our platform. This would leverage a mature ecosystem but cedes strategic control and risks lock-in to that framework's architecture and release cadence.
5. **Support Multiple Co-Equal SDKs:** Officially support and document several third-party SDKs. This offers maximum choice but makes it difficult for our own platform tools (e.g., a UI for creating agents) to provide a consistent, functional user experience, as they would need to target multiple, incompatible outputs.
6. **New, Minimal Red Hat Container/Service:** Provide an ultra-lightweight container that exposes a simple HTTP API for agent interaction and recommend users graduate to more powerful frameworks for complex needs.
7. **New, Minimal Red Hat SDK:** Provide an ultra-lightweight SDK designed for basic use cases and tutorials, while officially recommending that customers adopt comprehensive third-party frameworks for advanced applications.

## Decision

We will adopt **Option 7**. We will create a **new, minimal, lightweight Red Hat Agent SDK** and concurrently establish a strategy to **officially recommend and ensure compatibility with established third-party frameworks**.

The new Red Hat Agent SDK will be written in **Python**. The specific list of third-party frameworks we will recommend and ensure compatibility with will be addressed in one or more future ADRs.

The key characteristics of the Red Hat Agent SDK will be:

* **Minimalist Scope:** It will focus exclusively on implementing the core agent loop (state management, API calls, tool dispatching) as a reference. It is not intended to have complex features like chains, memory modules, or vector store integrations.
* **Enablement, Not Competition:** Its primary purpose is to serve as a clear, simple "golden path" for new users, tutorials, documentation, and basic proof-of-concept applications.
* **Reference Implementation:** It will act as the reference for how to correctly interact with the Llama Stack Responses API in an agentic fashion, providing a foundation that other tools can build upon or refer to.

This two-pronged approach (a minimal "first-step" SDK and a clear "next-step" recommendation of powerful external tools) provides the best balance of speed, user choice, and focused engineering effort.

## Status

Proposed

## Consequences

### Positive

* **Rapid Time-to-Market:** A minimal SDK is a fast way to deliver a functional agent construct to our users, allowing us to provide a complete end-to-end story quickly.
* **Empowers User Choice:** This strategy explicitly embraces the rich AI ecosystem. Customers with existing expertise in established frameworks can use their preferred tools, while new users have a simple, non-intimidating entry point.
* **Low Engineering Overhead:** By strictly limiting the scope of our own SDK, we avoid the massive maintenance burden of creating and supporting a full-featured framework. Engineering efforts are focused and contained.
* **Simplified Tooling:** Having a single, simple, Red Hat-owned SDK as a target greatly simplifies the development of any integrated tooling (e.g., agent creation wizards in the RHOAI console).
* **Avoids Containerization Complexity:** Choosing an SDK over a container image avoids the overhead of building, distributing, securing, and running a container for what is fundamentally client-side logic, simplifying the developer workflow.

### Negative

* **Weakens the "Unified Framework" Narrative:** This approach makes it harder to market Llama Stack or a Red Hat offering as a single, all-in-one agent framework. The story is more nuanced ("use our simple SDK to start, then use these other tools").
* **Risk of SDK Fragmentation and Confusion:** We must provide clear documentation and guidance to help users understand when to use the minimal Red Hat SDK and when it's time to "graduate" to a more powerful framework.
* **Limited to Python:** The decision to write the SDK only in Python will limit its direct usefulness for customers who prefer other languages. It also presents a challenge for our internal tooling teams who may use other languages like Go. We accept these trade-offs, acknowledging that most of the target AI/ML developer audience works primarily in Python and that workarounds can be found for internal tooling.
* **Potential for an Inadequate SDK:** There is a risk that our minimal SDK will be too limited even for slightly complex use cases, forcing a migration to another framework very early in the development process. The initial scope must be defined carefully to be useful.
* **Implied Support Burden:** By officially recommending third-party frameworks, we create a customer expectation of support. We will need to clearly define our support boundaries and invest resources in creating compatibility documentation, examples, and potentially addressing integration-related issues.
