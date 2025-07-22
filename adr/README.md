# Architecture Decision Records

The ADR is a lightweight record format intended to capture individual architecturally important decisions. They are meant to be easy to write - 10 minutes or less. They should be stored in the codebase they affect, go through peer review, and have a commit history.

This simple format, which is described below, has a surprising number of functions:

* **Decision making process**: by going through peer review with a formal approval process, it includes all maintainers and gives all perspectives a chance to be heard. There is a clear decision making process with a clear lifecycle - once an ADR meets whatever approval criteria the maintainers have chosen, it is merged and the decision is done. If new information comes to light that causes the maintainers to reconsider the decision, then that is simply a new ADR.
* **Institutionalized knowledge and transparency**: Not everyone will comment on every ADR, but the transparency of the mechanism should serve to keep everyone informed and encode tribal knowledge into writing. This also builds resilience - there should ideally never be decision making that is blocked by someone being sick or on vacation. The maintainers should always be able to make significant decisions.
* **Distribute design authority**: As contributors become familiar and comfortable with the ADR mechanism, every contributor has an equal tool to propose architecturally significant changes. This encourages autonomy, accountability, and ownership.
* **Onboarding and training material**: A natural consequence of it being easy to write an ADR and getting into the habit of doing so is that new contributors can simply read the record of existing ADRs to onboard.
* **Knowledge sharing**: The peer review phase allows sharing of expertise between contributors.
* **Fewer meetings**: As decision making becomes asynchronous and as social norms form around the process, decision making should become more and more efficient.

## When to write an ADR

* A decision is being made that required discussion between two or more people.
* A decision is being made that required significant investigation.
* A decision is being proposed for feedback / discussion.
* A decision is being proposed that affects multiple components.

## Template

[Here](template.md).

## Related Reading

* [Suggestions for writing good ADRs](https://github.com/joelparkerhenderson/architecture-decision-record?tab=readme-ov-file#suggestions-for-writing-good-adrs)
* [ADRs at RedHat](https://www.redhat.com/architect/architecture-decision-records)
* [ADRs at Amazon](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html)
* [ADRs at GitHub](https://adr.github.io/)
* [ADRs at Google](https://cloud.google.com/architecture/architecture-decision-records)

## Disclaimer: Subject to Change

The Architecture Decision Records (ADRs) and pull requests (PRs) in this directory, as well as any comments made on them, reflect current intentions and priorities at the time of writing and are shared for informational and community engagement purposes only. They, and any discussion related to them, do not represent a binding commitment to deliver any particular feature, fix, or enhancement.

The maintainers reserve the right to revise, postpone, or abandon any listed items at any time and without notice, based on evolving technical requirements, user feedback, or project direction.

Nothing in this directory should be interpreted as:

* A product guarantee;

* A promise of delivery within a specific timeframe;

* A contractual obligation to implement specific features.

Users and contributors should not rely on these ADRs when making operational or business decisions. For the most accurate and up-to-date information, please refer to the project's official documentation and release notes.