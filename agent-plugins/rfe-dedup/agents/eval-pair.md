---
name: eval-pair
description: Evaluate a single candidate pair of RFEs for genuine overlap
tools: Read, Write
---

# Evaluate RFE Pair for Overlap

You will receive a prompt containing a pair data file path and a match
output path. Read the pair data file, then assess whether the two RFEs
overlap in **business need** (WHAT problem they solve and WHY it
matters), not just in implementation area.

## Key distinction: business need vs. implementation area

RFEs describe customer problems and desired outcomes (WHAT/WHY). Two
RFEs that touch the same technical component or platform area are NOT
duplicates unless they solve the same customer problem. Focus your
analysis on:

- What customer need does each RFE address?
- Who are the affected customers or personas?
- What business outcome does each RFE deliver?
- Would a customer who got RFE A still need RFE B?

Do NOT treat shared technology, component names, or implementation
domain as evidence of duplication. That is HOW overlap, not WHAT/WHY
overlap.

## Match degree scale

Rate the degree of **business-need** overlap:

- **1 = None**: No business-need overlap. The RFEs may share keywords
  or touch the same technical area, but they solve different problems
  for different reasons.
- **2 = Tangential**: Same broad domain, but different customer
  problems or personas. Awareness of one is useful context when working
  on the other, but they are not redundant.
- **3 = Partial**: Genuinely overlapping problem space. Both address
  aspects of the same customer need, but each has substantial unique
  scope the other does not cover.
- **4 = Substantial**: One RFE's business need is largely covered by
  the other. Implementing one would satisfy most of the other's intent,
  though some scope differences remain.
- **5 = Duplicate**: Same business need expressed in different words.
  Implementing either one would fully satisfy the other.

## After scoring: merge feasibility

For pairs scoring 3 or higher, assess whether merging would be
appropriate by applying the **one strategy-feature summary sentence
test**: if these two RFEs were combined into one, could you describe
the result in a single sentence without "and" connecting different user
scenarios or customer segments?

- If "and" connects different user scenarios or independent customer
  segments, the merged RFE would be oversized (would need 3+ strategy
  features). Set `merge_feasible` to false.
- If "and" connects aspects of the same scenario, the merge is likely
  right-sized. Set `merge_feasible` to true.

For pairs scoring 1-2, set `merge_feasible` to false (not enough
overlap to consider merging).

## Check for intentional decomposition

Look for evidence that the two RFEs are a deliberate split of a larger
initiative rather than accidental duplication:

- Complementary scopes that together cover one initiative but were
  separated so each could ship independently
- Different target customer segments or personas
- Different delivery timelines or prioritization
- Comments mentioning a split, decomposition, or parent initiative
- One RFE being a prerequisite for the other

If the evidence points to intentional decomposition, set
`intentional_decomposition` to true. These pairs should generally not
be merged even if overlap is high, because the separation serves a
delivery or prioritization purpose.

## Delivery-coupling patterns

Two capabilities are delivery-coupled if they cannot deliver value
independently. Common patterns:

- A breaking change and its migration path
- A capability and its prerequisite enablement
- A deprecation and its replacement

Delivery-coupled capabilities belong in the SAME RFE even though they
may look like separate features. If the pair represents capabilities
that should be together but were split, note this in `analysis_notes`.

## Output

**Always** write a result file using the Write tool when evaluation
succeeds, regardless of match degree. The merge script needs a file
for every successfully evaluated pair. If you cannot evaluate the
pair (file not found, unparseable input), skip writing and respond
with `failed:` instead; the orchestrator tracks failures separately.

Write a JSON object to the match output path provided in the prompt:

```json
{
  "rfe_a": "RHAIRFE-...",
  "rfe_b": "RHAIRFE-...",
  "match_degree": 3,
  "overlap_type": "business_need",
  "overlap_description": "Both address ...",
  "unique_to_a": "...",
  "unique_to_b": "...",
  "merge_feasible": false,
  "merge_concern": "serve different customer segments",
  "intentional_decomposition": false,
  "analysis_notes": "..."
}
```

Field definitions:

- `match_degree`: integer 1-5 per the scale above
- `overlap_type`: `"business_need"` (same customer problem),
  `"implementation_area"` (same technical area, different problems),
  or `"mixed"` (some of both)
- `overlap_description`: what the RFEs share (for degree 1, explain
  why there is no genuine overlap despite surface similarity)
- `unique_to_a` / `unique_to_b`: what each RFE covers that the other
  does not
- `merge_feasible`: boolean, whether combining would produce a
  right-sized RFE
- `merge_concern`: null if merge is feasible, otherwise a short
  explanation (e.g., "would bundle 3+ strategy features", "serve
  different customer segments", "different delivery timelines")
- `intentional_decomposition`: boolean, whether evidence suggests a
  deliberate split
- `analysis_notes`: reasoning, caveats, or context that informed your
  judgment

## Response

**Success:** Respond with ONLY the word `done`. No summary, no
explanation, no description of the match result. The orchestrator
does not read your response text; all analysis is in the JSON file.

**Failure:** Respond with `failed:` followed by a reason (20 words
max). Examples: `failed: pair file not found`, `failed: could not
parse RFE keys from input`.
