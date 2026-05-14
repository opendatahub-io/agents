---
name: report-group
description: Synthesize a duplicate analysis report section for one group of related RFEs
tools: Read, Write
---

# Synthesize Group Report Section

You will receive a prompt containing: a group data file path, a report
output path, a group number, a member count, and a Jira browse URL.

Read the group data file using the Read tool. The file contains member
data and pairwise match data including overlap type, merge feasibility,
and intentional decomposition indicators.

Format all RFE keys as markdown hyperlinks using the Jira browse URL
from the prompt: `[RHAIRFE-NNN](<jira_browse_url>/RHAIRFE-NNN)` in
tables, prose, and everywhere else they appear.

## Choosing a recommendation

Use the pairwise match data to choose ONE recommendation for the
group. The recommendation must account for both the degree of overlap
and whether merging would produce a well-formed RFE.

### Merge

Recommend **Merge** only when ALL of these conditions hold:

- All pairwise match degrees in the group are 4-5 (Substantial or
  Duplicate)
- `overlap_type` is `"business_need"` on all pairs (not just
  `"implementation_area"`)
- `merge_feasible` is true on all pairs, meaning the combined RFE
  would still be right-sized (expressible as a single strategy-feature
  summary sentence)
- No pair has `intentional_decomposition: true`

If any condition fails, do not recommend Merge even if match degrees
are high.

### Well-decomposed

Recommend **Well-decomposed** when the group appears to be an
intentional, well-executed decomposition of a larger initiative:

- Multiple pairs have `intentional_decomposition: true`
- Members have complementary (non-redundant) scopes
- `merge_feasible` is false because the combined scope would be
  oversized
- The group collectively covers a coherent initiative, but each member
  can ship independently

This recommendation tells the human reviewer that no action is needed;
the overlap is by design.

### Cross-reference

Recommend **Cross-reference** when there is substantial business-need
overlap but merging is not appropriate:

- Match degrees are 3-4 with `overlap_type: "business_need"` or
  `"mixed"`
- But `merge_feasible` is false (combined result would be oversized),
  OR members serve different customer segments or delivery timelines
- The RFEs should reference each other so work is coordinated, but
  they should remain separate

### Review

Recommend **Review** when human judgment is needed:

- Pairwise assessments within the group are inconsistent (e.g., some
  pairs are degree 4 while others are degree 2)
- `overlap_type` is `"mixed"` or varies across pairs
- There is moderate overlap (degree 3) without clear signals either
  way on merge feasibility
- Any other ambiguous situation

## Report section format

Use the Write tool to write the report section to the report output
path provided in the prompt:

1. A heading: `## Group <group_number>: <descriptive theme> (<member_count> RFEs)`
2. **Members:** table of keys (as Jira hyperlinks) with titles
3. **Overlap Matrix:** table showing pairwise match degrees and
   overlap types (e.g., "4 / business_need", "3 / mixed")
4. **Common Theme:** what connects all members
5. **Shared Across All:** bullet list of shared aspects
6. **Unique Aspects:** one bullet per member describing its unique
   scope
7. **Merge Feasibility:** whether combining all members would produce
   a right-sized RFE, citing the merge_concern values from pairwise
   data if merge is not feasible
8. **Recommendation:** one of Merge, Well-decomposed, Cross-reference,
   or Review, with a brief rationale explaining why this recommendation
   was chosen over the alternatives

End the section with a `---` separator.

## Companion JSON

In addition to the markdown report, write a companion JSON file at
the same path with `.json` extension instead of `.md`. For example,
if the report path is `<run_dir>/reports/report_01.md`, write JSON
to `<run_dir>/reports/report_01.json`.

The JSON must contain:

```json
{
  "group_number": 1,
  "recommendation": "Merge",
  "recommendation_rationale": "All pairs degree 4-5 with business_need overlap...",
  "common_theme": "Short theme description",
  "members": [
    {"key": "RHAIRFE-1234", "summary": "Title of the RFE"}
  ],
  "merge_candidates": [
    {
      "rfe_a": "RHAIRFE-1234",
      "rfe_b": "RHAIRFE-1235",
      "match_degree": 4,
      "match_degree_label": "Substantial",
      "overlap_type": "business_need",
      "merge_feasible": true,
      "intentional_decomposition": false
    }
  ]
}
```

Rules for the JSON:

- `merge_candidates` includes all pairwise matches with
  `match_degree >= 3`. If a field is missing from the pairwise data
  (e.g., `overlap_type` or `merge_feasible`), use `null`.
- `recommendation` must be exactly one of: `"Merge"`,
  `"Well-decomposed"`, `"Cross-reference"`, `"Review"`.
- `members` lists every group member with key and summary.

## Response protocol

Write both the `.md` and `.json` files, then respond `done`.
Respond `failed:` plus a reason (20 words max) if anything went wrong.
