---
name: rfe.dedup
user-invocable: true
allowed-tools: Agent, Bash, Read, Write, Glob, Grep, AskUserQuestion
description: >
  Analyze a set of Jira RFEs for partial or complete duplicates. Takes a
  query description, fetches matching RFEs, uses semantic embeddings to find
  candidate matches, then evaluates overlap in detail.
---

# RFE Duplicate Analysis

Analyze a set of Jira RFEs for duplicate or overlapping intent, even when
worded very differently. Produces a report describing the degree of overlap,
what's shared, and what's unique for each group of related RFEs.

## Prerequisites

The following must be available:

- `JIRA_API_TOKEN` environment variable set with a Jira API token
- Jira CLI configured (`~/.config/.jira/.config.yml`) OR `JIRA_SERVER` and
  `JIRA_USER` environment variables set
- Python packages: `requests`, `sentence-transformers`, `faiss-cpu`, `numpy`

If any prerequisite is missing, tell the user what's needed and stop.

## Input

The user provides a description of which RFEs to analyze. Examples:

- "All RHAIRFE tickets with status New or Refinement Needed"
- "project = RHAIRFE AND component = AgentDev"
- "RHAIRFE tickets tagged 3.5-candidate"

## Step 1: Construct the JQL query

Translate the user's description into a valid JQL query. Standard fields
(project, status, component, labels, priority, issuetype, assignee,
created, updated) work by name. Examples:

| User says | JQL |
|-----------|-----|
| "RHAIRFE tickets in New status" | `project = RHAIRFE AND status = New` |
| "AgentDev component, status New or Stakeholder review" | `project = RHAIRFE AND component = AgentDev AND status IN (New, "Stakeholder review")` |
| "3.5-candidate RFEs" | `project = RHAIRFE AND labels = 3.5-candidate` |

If the user references a field you don't recognize as a standard Jira
field (e.g., "Target Version", "Color Status", "Team"), read the custom
field reference at `$SKILL_DIR/references/jira_fields.md` for the
`cf[ID]` mapping before constructing the query.

If the user's description is ambiguous, ask for clarification using
`AskUserQuestion` before proceeding.

Show the user the constructed JQL and confirm before fetching.

## Step 1b: Create a run directory

Each run stores its artifacts in a unique directory under `.local/`.

First, compose a concise 2–5 word description of what the user is
trying to do — not a reformulation of the JQL, but a plain-language
label for the analysis (e.g., `"new rhairfe rfes"`,
`"agentdev component"`, `"3.5 candidate backlog"`). Use the user's
own words where possible. Then run:

```bash
python3 "$SKILL_DIR/scripts/create_run_dir.py" --name "<your description>"
```

The script normalizes the description to a lowercase hyphen-separated
slug, prepends `dedup-`, appends a numeric suffix if the name already
exists, creates the directory, and prints the path to stdout.

Capture the printed path — all subsequent steps use it as `<run_dir>`.

## Step 2: Fetch RFEs

Run the fetch script. The `SKILL_DIR` variable below refers to the directory
containing this SKILL.md file.

```bash
python3 "$SKILL_DIR/scripts/fetch_rfes.py" \
  --jql "<the JQL query>" \
  --output-dir "<run_dir>"
```

This writes one JSON file per RFE into `<run_dir>/rfes/` (e.g.,
`rfes/RHAIRFE-1234.json`) plus a `rfes/_meta.json` for caching.
Subsequent runs with the same JQL reuse cached results if less than
4 hours old.

Report how many RFEs were fetched. If zero, tell the user and stop.
If the script fails due to missing credentials, tell the user what
environment variables to set.

Use `AskUserQuestion` to confirm before proceeding. Show the count and
ask whether to continue. This catches cases where the JQL didn't match
the user's intent (e.g., unexpectedly few or many results). If the user
declines, ask what to adjust (JQL, status filter, etc.) and return to
Step 1.

## Step 3: Find candidate duplicate pairs

Run the candidate detection script:

```bash
python3 "$SKILL_DIR/scripts/find_candidates.py" \
  --rfes-dir "<run_dir>/rfes" \
  --output "<run_dir>/candidates.json" \
  --threshold 0.8
```

This reads individual RFE files from the `rfes/` directory, loads the
granite-embedding-english-r2 model (149M params, ~600MB download on
first run), embeds each RFE's text, and uses FAISS to find
semantically similar pairs. Results are sorted by similarity score
and written to `candidates.json`.

If the script reports zero candidates on stderr, report that no
potential duplicates were detected and stop.

## Step 3a: Filter linked pairs

Filter out candidate pairs where the two RFEs already have a known
Jira relationship (split, duplicate, or cloner links):

```bash
python3 "$SKILL_DIR/scripts/filter_candidates.py" \
  --candidates "<run_dir>/candidates.json" \
  --rfes-dir "<run_dir>/rfes"
```

This removes pairs where both RFEs belong to the same "link family"
— either directly linked or transitively connected via split/duplicate/
cloner relationships (e.g., if A was split into B and C, the B–C pair
is also filtered even though B and C have no direct link).

Parse the remaining candidate count from the script's stderr output
(the line ending with `N candidates remaining`). Do NOT load
`candidates.json` — it can be very large. Use this filtered count —
not the original find_candidates count — for the volume guidance below.

**Volume guidance:** If there are more than 250 candidates, tell the
user the count and ask how they'd like to proceed. Include a time
estimate for each option using this formula:

    estimated minutes ≈ pairs / speed_factor

where `speed_factor` depends on the model running this skill:
- Opus models: speed_factor = 5
- Sonnet models: speed_factor = 10
- Haiku models: speed_factor = 20

Present three options with estimates:

1. **Analyze top 250 candidates** — covers the strongest matches
   (~N minutes)
2. **Analyze all candidates** — most thorough (~N minutes)
3. **Use a smaller list** — keeps only the top N, suggest a round
   number like 50 or 100 (~N minutes)

The user's choice becomes the `--max-pairs` argument in Step 3b.
If 250 or fewer candidates, proceed directly to Step 3b without
asking.

## Step 3b: Prepare pairs for evaluation

Run the pair preparation script to extract and format the candidate
pairs' full text for efficient evaluation. Pass `--max-pairs` with
the user's chosen count from Step 3. The script defaults to a cap of
500 pairs when neither `--max-pairs` nor `--no-limit` is given:

```bash
python3 "$SKILL_DIR/scripts/prepare_pairs.py" \
  --candidates "<run_dir>/candidates.json" \
  --rfes-dir "<run_dir>/rfes" \
  --output-dir "<run_dir>" \
  --max-pairs <N>
```

Pass `--no-limit` instead of `--max-pairs` to prepare all candidates.

This selects the top N candidates by similarity score, then creates
individual files in `<run_dir>/pairs/`: `pair_001.md`,
`pair_002.md`, etc., one per candidate pair, each containing the
formatted RFE text ready for evaluation.

## Step 4: Evaluate candidate pairs

List the files in `<run_dir>/pairs/` to get the pair count. For each
pair, evaluate whether it represents a genuine overlap in **business
need** (WHAT customer problem it solves and WHY it matters), not just
surface-level keyword similarity or shared implementation area. Each
evaluation also assesses whether merging would produce a right-sized
RFE and whether the pair looks like an intentional decomposition.

### Parallel evaluation with Agent tool

Evaluate each pair in its own Agent subagent to keep context windows
small. Launch agents in waves of 10 — send all 10 Agent tool calls
in a single message so they run concurrently, wait for all 10 to
complete, then launch the next 10, and so on until all pairs are
evaluated. Do NOT use `run_in_background` — foreground agents sent
together already run in parallel, and background notifications cause
streaming errors that break subsequent tool calls.

For each pair file, invoke the `Agent` tool with:
- `subagent_type`: `"rfe-dedup:eval-pair"`
- `description`: a short label like `"Eval pair 001"`
- `prompt`: a message providing the file paths, e.g.:
  `Read the pair data file at <run_dir>/pairs/pair_001.md and write
  the match result to <run_dir>/match_results/match_001.json`

The `eval-pair` agent is provided by this plugin and knows how to
read pair files, assess overlap, and write match results. You do NOT
need to read the agent file or include its instructions in the
prompt. Claude Code loads the agent definition automatically via
`subagent_type`.

Do NOT specify a `model` parameter on Agent calls — let subagents
inherit the parent model. The user chose the orchestrating model
for its judgment quality; downgrading subagents undermines the
analysis.

Do NOT read pair files in the main context — each agent reads its
own pair file, keeping the orchestration context small.

Each agent writes its own match result directly to disk and responds
with only `done`. If an agent fails, it responds with `failed:`
followed by a short reason and does NOT write an output file.

After each wave, check agent responses and count any that start with
`failed:`. Track the cumulative failure count across all waves. Then
count match files to track progress:

```bash
python3 "$SKILL_DIR/scripts/count_artifacts.py" --dir "<run_dir>/match_results"
```

### Merge match results

After all waves complete, merge the individual match files:

```bash
python3 "$SKILL_DIR/scripts/merge_matches.py" \
  --match-dir "<run_dir>/match_results" \
  --output "<run_dir>/confirmed_matches.json"
```

If there are no confirmed matches, report that and stop.

## Step 5: Form groups

Run the group formation script:

```bash
python3 "$SKILL_DIR/scripts/form_groups.py" \
  --input "<run_dir>/confirmed_matches.json" \
  --rfes-dir "<run_dir>/rfes" \
  --output-dir "<run_dir>" \
  --min-degree 3
```

This connects pairwise matches into groups using only degree 3+
(Partial or stronger) edges. Degree 2 (Tangential) matches are
excluded from group edges but still included as context in group
files. The script writes individual files in `<run_dir>/groups/`:
`group_01.md`, `group_02.md`, etc., each containing the full member
data and all pairwise match data (degree 2+), ready for a
report-group agent. It also writes `<run_dir>/groups_summary.json`
with structured group metadata, cross-group references, and
ungrouped RFEs.

## Step 5a: Fill missing intra-group pairs

When candidate pairs are truncated (e.g., top 250), groups formed by
connected components often have unevaluated intra-group pairs. Run
this script to identify and prepare them. The script defaults to a
cap of 500 gap pairs; pass `--no-limit` to prepare all:

```bash
python3 "$SKILL_DIR/scripts/find_missing_pairs.py" \
  --confirmed-matches "<run_dir>/confirmed_matches.json" \
  --rfes-dir "<run_dir>/rfes" \
  --output-dir "<run_dir>" \
  --min-degree 3
```

Parse the gap pair count from stderr (`Found N missing intra-group
pairs`). If zero, skip ahead to Step 6.

If gap pairs were found, evaluate them using the same wave-of-10
eval-pair agent pattern as Step 4. For each file in
`<run_dir>/gap_pairs/`, invoke the Agent tool with:
- `subagent_type`: `"rfe-dedup:eval-pair"`
- `description`: a short label like `"Gap eval 001"`
- `prompt`: pointing to the gap pair file and gap match results dir:
  `Read the pair data file at <run_dir>/gap_pairs/pair_001.md and
  write the match result to <run_dir>/gap_match_results/match_001.json`

After all gap evaluations complete, merge the gap results:

```bash
python3 "$SKILL_DIR/scripts/merge_matches.py" \
  --match-dir "<run_dir>/gap_match_results" \
  --output "<run_dir>/gap_confirmed.json"
```

If there are new confirmed matches, concatenate them with the original
confirmed matches and re-form groups:

```bash
python3 -c "
import json; from pathlib import Path
orig = json.loads(Path('<run_dir>/confirmed_matches.json').read_text())
gap = json.loads(Path('<run_dir>/gap_confirmed.json').read_text())
combined = (orig if isinstance(orig, list) else orig.get('matches', [])) + \
           (gap if isinstance(gap, list) else gap.get('matches', []))
Path('<run_dir>/confirmed_matches.json').write_text(json.dumps(combined, indent=2))
"
```

Then re-run group formation to include the new pairwise data:

```bash
python3 "$SKILL_DIR/scripts/form_groups.py" \
  --input "<run_dir>/confirmed_matches.json" \
  --rfes-dir "<run_dir>/rfes" \
  --output-dir "<run_dir>" \
  --min-degree 3
```

## Step 6: Generate the report

### Parallel group synthesis with Agent tool

List the files in `<run_dir>/groups/` to get the group count. For
each group, launch an Agent subagent to synthesize a group-level
report section. Launch agents in waves of 10 — send all 10 Agent
tool calls in a single message so they run concurrently, wait for
all 10 to complete, then launch the next 10, and so on until all
groups are covered. Do NOT use `run_in_background`.

**Before the first wave**, get member counts for all groups:

```bash
python3 "$SKILL_DIR/scripts/group_metadata.py" --groups-dir "<run_dir>/groups"
```

This prints TSV lines: `<group_num>\t<member_count>`. Use these
values when constructing agent prompts below.

For each group file, invoke the `Agent` tool with:
- `subagent_type`: `"rfe-dedup:report-group"`
- `description`: a short label like `"Report group 01"`
- `prompt`: a message providing all needed values, e.g.:
  `Read the group data file at <run_dir>/groups/group_01.md.
  Group number: 1. Member count: 3.
  Jira browse URL: $JIRA_SERVER/browse.
  Write the report section to <run_dir>/reports/report_01.md`

The `report-group` agent is provided by this plugin and knows how to
read group files, format the report section, and write it to disk.
You do NOT need to read the agent file or include its instructions
in the prompt. Claude Code loads the agent definition automatically
via `subagent_type`.

Do NOT specify a `model` parameter on Agent calls — let subagents
inherit the parent model.

Do NOT read group files in the main context — each agent reads its
own group file, keeping the orchestration context small.

Each agent writes its report section (both `.md` and `.json`) directly
to disk and responds with only `done`. After each wave, count report
files to track progress:

```bash
python3 "$SKILL_DIR/scripts/count_artifacts.py" --dir "<run_dir>/reports"
```

### Assemble the final report

After all agents complete, assemble the report:

```bash
python3 "$SKILL_DIR/scripts/assemble_report.py" \
  --reports-dir "<run_dir>/reports" \
  --output "<run_dir>/dedup_report.md" \
  --groups-summary "<run_dir>/groups_summary.json" \
  --jql "<the JQL query>" \
  --date "<today's date>" \
  --rfe-count <count> \
  --group-count <count>
```

This produces two outputs: `dedup_report.md` (human-readable markdown)
and `dedup_report.json` (structured summary with group metadata,
cross-group references, and per-group recommendations).

Tell the user where the report was written and provide a brief summary
of the findings (how many groups, notable overlaps, key recommendations).
If any eval-pair agents failed during Steps 4 or 5a, include the
failure count (e.g., "2 of 250 pair evaluations failed").
