# ADR: Adopt a Minimal Guidance and Ecosystem Strategy for Agents

## Context

Following the decision in [ADR: Adopt Llama Stack Responses API for Agentic MCP](https://github.com/opendatahub-io/agents/pull/1) to adopt the Llama Stack Responses API, we committed to enabling users to build agentic reasoning systems using the Responses API.  This ADR addresses the critical follow-up question: what specific capabilities will we provide and/or recommend for that purpose?

The goal is to provide a solution that enables developers, offers a clear path for simple use cases, and integrates well with the broader AI ecosystem, all while managing Red Hat's engineering investment and long-term strategy.

We considered several options:

1. **Extend Llama Stack Client SDK:** Add the agent logic directly into the official Llama Stack client. This would create a strong, unified story but conflicts with the client's design as a thin, auto-generated layer.  Any code that is not auto-generated from the Open API definitions must be manually created and maintained in several programming languages.  Today, only the Python Llama Stack Client SDK includes the Agents APIs, due to this maintenance burden.
2. **New, Full-Featured Red Hat SDK:** Build a comprehensive, competitive agent framework from the ground up. This offers maximum control but requires a very significant, long-term engineering investment. Also, even if it was done well, it would be difficult to drive adoption due to strong competition in this space.
3. **New, Full-Featured Red Hat Container/Service:** The same as above, but delivered as a containerized HTTP service. This could simplify agent sharing and support a broader assortment of programming languages, but it adds operational complexity for developers.
4. **Adopt a Single Third-Party SDK:** Formally adopt, package, and recommend a single existing framework (e.g., LangChain) as the "official" way to build agents on our platform. This would leverage a mature ecosystem but cedes strategic control and risks lock-in to that framework's architecture and release cadence.
5. **Support Multiple Co-Equal Third-Party SDKs:** Officially support and document several third-party SDKs. This offers more choice but makes it difficult for our own platform tools (e.g., a UI for creating agents) to provide a consistent, functional user experience, as they would need to target multiple, incompatible outputs.
6. **New, Minimal Red Hat Container/Service:** Provide an ultra-lightweight container that exposes a simple HTTP API for agent interaction and recommend users graduate to more powerful frameworks for complex needs.  Note, that the decision of where to host that capability and what to brand it as is outside the scope of this ADR, but in principle it could be branded as "part of Llama Stack" if the Llama Stack maintainers would agree to that.
7. **New, Minimal Red Hat Python SDK Plus Recommend Third-Party SDKs:** Provide an ultra-lightweight Python SDK designed for basic use cases and tutorials, while officially recommending that customers adopt comprehensive third-party frameworks for advanced applications.  As above, branding for this SDK is outside the scope of this ADR.
8. **User Developed Agents Plus Recommend Third-Party SDKs:** Provide users guidance on how to do agentic reasoning using the Responses API (via the OpenAI and/or Llama Stack clients) directly.   As above, we would also recommend that power users consider third-party SDKs if they don't want to build their own agentic framework.

## Decision

We will adopt **Option 8** (User Developed Agents Plus Recommend Third-Party SDKs). We will provide users with guidance on how to use the Responses API themselves and not provide a supported Agent construct.

The user guidance could wind up being a lot like a minimal SDK, i.e., sample code showing how to make a simple/basic Agent object that doesn't do much, but packaging it as documentation rather than a library encourages users to make it their own instead of accepting its limitations.  However, an even simpler version of the guidance could just show code for invoking the Responses API and leave it up to the user to wrap it in an object or not as they wish.  The details of the guidance will determined by the author of the guidance.

We will also **officially recommend and ensure compatibility with established third-party frameworks**.  The specific list of third-party frameworks we will recommend and ensure compatibility with will be addressed in one or more future ADRs.  Those ADRs will also address the issue of whether any frameworks will be included in the product builds and/or supported.  If we don't include or support any frameworks, then the recommendations to use them is likely to be very gentle, e.g., "Here are a list of agent frameworks that have been reported to work with Llama Stack.  We recommend that users investigate one or more of these and see if it meets their needs."

## Status

Proposed

## Consequences

### Positive

* **Rapid Time-to-Market:** This approach limits our development commitments, allowing us to provide a complete end-to-end story quickly.
* **Empowers User Choice:** This strategy explicitly embraces the rich AI ecosystem. Users with existing expertise in established frameworks can use their preferred tools, while users without any prior AI experience have simple, non-intimidating guidance on how to start without any agent framework.
* **Low Engineering Overhead:** Since we are not producing an SDK, we avoid the massive maintenance burden of creating and supporting a full-featured framework. Engineering efforts are focused and contained.
* **Simplified Tooling:** Having the Responses API alone as a stable target greatly simplifies the development of any integrated tooling (e.g., agent creation wizards in the RHOAI console).

### Negative

* **Weakens the "Unified Framework" Narrative:** This approach makes it harder to market Llama Stack or a Red Hat offering as a single, all-in-one agent framework. The story is more nuanced ("use the Responses API directly for simple agents and other tools for more complex ones").
* **Risk of SDK Fragmentation and Confusion:** We must provide clear documentation and guidance to help users understand when to call the Responses API directly following our guidance and when it's time to "graduate" to a more powerful framework.
* **Limited Number of Programming Languages:** To the extent that our guidance includes example code, it will only provide such examples for a small number of programming languages (definitely Python and maybe one or two others). This will limit its usefulness to anyone who wants to use a different language.
* **Potential for an Inadequate Guidance:** There is a risk that our guidance will be too limited even for slightly complex use cases, forcing a migration to a third-party framework very early. This can be mitigated by ensuring the guidance is explicit about its limitations and includes clear criteria for deciding when to use a third-party agent framework.
* **Support Burden for Third-Party Framework Compatibility:** When we recommend that users consider third-party frameworks, some customers will expect support if they run into problems. We can reduce but not eliminate such expectations by wording the recommendation carefully. Furthermore, when we claim compatibility with de facto API standards, all customers have a reasonable expectation that we will fix defects or limitations in our compatibility.
