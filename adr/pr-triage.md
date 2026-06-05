# ADR: Build a PR Triage Plugin to Help Reviewers Identify Low-Quality AI-Generated Pull Requests

## Context

Open-source maintainers are increasingly overwhelmed by low-quality, AI-generated pull requests. Contributors point bots at open issues, generate PRs with minimal human oversight, and submit them for review. The burden then falls on maintainers to determine whether the PR is worth reviewing at all, let alone correct.

This problem is acute in high-traffic upstream projects like vLLM, where maintainers report spending hours per day reviewing PRs that turn out to be "AI slop," including PRs that:

- Provide fabricated evidence of validation (e.g., claiming an issue author confirmed a fix when they didn't)
- Reference hallucinated artifacts (e.g., HuggingFace model names that don't exist)
- Submit unit tests that pass but test scenarios that don't occur in real-world usage
- Propose changes that are entirely unrelated to the actual root cause of the reported issue
- Generate back-and-forth comment spam with review bots without producing useful output

The core challenge is **separating signal from noise**: identifying PRs where a human has taken genuine ownership and invested effort in testing and validating the change, versus drive-by submissions where a bot generated code with no meaningful human vetting.

This is not strictly a code quality problem. A PR can contain syntactically correct, well-structured code and still be a waste of reviewer time if it doesn't address the actual problem, references nonexistent artifacts, or provides misleading justification for merging.

### Prior art and community approaches

Different upstream communities are experimenting with their own solutions:

- **Vouch systems**: Some NVIDIA repos (e.g., OpenShell) require first-time contributors to be vouched for by existing contributors before PRs are reviewed
- **AGENTS.md tweaks**: vLLM committers have adjusted their AGENTS.md to discourage certain bot behaviors
- **Auto-closing**: Some repos auto-close PRs from unrecognized contributors

These are repo-specific governance decisions. This tool does not replace them. Instead, it gives individual reviewers a quick assessment of whether a PR is likely worth their time, based on observable signals.

## Decision

We will build a **pr-triage** Claude Code plugin in the `agent-plugins/` directory that scores pull requests against a heuristic rubric to help reviewers prioritize their time.

### Heuristic rubric

The rubric is organized into negative signals (indicators of low-quality or bot-generated PRs) and positive signals (indicators that a human invested effort). Each signal is independently assessed and contributes to an overall readiness score.

#### Negative signals

| ID | Signal | What to check |
|----|--------|---------------|
| N1 | **Single commit** | PR contains exactly one commit, suggesting a single bot generation pass with no iteration. *Note: this signal is controversial. Many experienced developers rebase to a single commit or commit only when the work is complete. This signal may be dropped during feature selection (see Phase 3) if it proves unpredictive.* |
| N2 | **No linked issue** | PR does not reference an existing issue; the change may be something nobody asked for |
| N3 | **Hallucinated references** | PR description or comments reference HuggingFace models, repos, commits, or other artifacts that don't exist |
| N4 | **Third-person self-reference** | PR description refers to the contributor in the third person (e.g., "The developer implemented..."), a common LLM generation pattern |
| N5 | **Misleading validation claims** | PR claims the fix was validated or confirmed by specific people without evidence, or points to tests that don't exercise real-world scenarios |
| N6 | **Unrelated fix** | The proposed changes don't logically address the stated problem; the real fix is elsewhere |
| N7 | **No prior contributions** | Contributor has no previously merged PRs in this repo |
| N8 | **Bulk submission pattern** | Contributor has multiple open PRs submitted in a short time window, suggesting automated mass submission |
| N9 | **Bot interaction spam** | PR comment history is dominated by back-and-forth with automated review bots with no substantive human discussion |
| N10 | **Template/boilerplate description** | PR description follows a rigid LLM-generated template (e.g., "Summary / Changes / Testing" with generic content). *Note: repos that use PR templates will trigger this signal on every PR, making it useless. This signal may be dropped during feature selection (see Phase 3) if it proves unpredictive.* |

#### Positive signals

| ID | Signal | What to check |
|----|--------|---------------|
| P1 | **Multiple sequential commits** | PR shows iterative development across multiple commits, suggesting human refinement |
| P2 | **Linked to an open issue** | PR references an existing issue that other users have reported or commented on |
| P3 | **Contributor track record** | Contributor has previously merged PRs in this repo |
| P4 | **Sustained engagement** | Contributor has a history of engagement in this repo over time (not a drive-by) |
| P5 | **Evidence of manual testing** | PR description or comments include reproduction steps, test output, or screenshots that appear genuine |
| P6 | **Documentation PR** | PR is docs-only; low risk, potentially high value, and may reduce future issues |
| P7 | **Small, focused diff** | Change is small and tightly scoped, making it easier to review |
| P8 | **Substantive discussion** | PR has meaningful human discussion in comments (not just bot exchanges) |

### Scoring model and calibration

#### The problem with equal weights

Not all signals carry equal weight. A hallucinated HuggingFace model reference (N3) is near-certain evidence of a bad PR, while a single commit (N1) is a weak signal that many legitimate PRs share. Simply summing detected signals would produce a score dominated by whichever category (positive or negative) has more checklist items, not by which signals actually predict reviewer-assessed quality.

The goal is a score that approximates: **"If an experienced maintainer glanced at this PR for 60 seconds, would they decide it's worth a full review?"**

#### Phased calibration approach

**Phase 0: Feature extraction (no model yet)**

Before any scoring, the tool needs to reliably extract each signal as a structured feature. Each heuristic produces:

- `detected`: boolean (or null if inconclusive)
- `confidence`: float 0.0 to 1.0 (how certain is the detection itself)
- `evidence`: string (what was observed)
- `raw_value`: numeric where applicable (e.g., commit count, days since first contribution, number of open PRs from this author)

Some signals are binary (N3: a referenced model either exists or it doesn't), while others are continuous (P7: diff size in lines, P4: days of contributor activity). The feature vector should preserve the continuous values rather than thresholding them into booleans prematurely, because the regression model can learn its own thresholds.

**Phase 1: Expert-assigned tiers (cold start)**

Before we have data, we assign signals to three tiers based on domain judgment:

| Tier | Weight | Signals | Rationale |
|------|--------|---------|-----------|
| Strong negative | -3 | N3 (hallucinated refs), N5 (misleading validation), N6 (unrelated fix) | These are near-certain indicators of a bad PR. Any one of them is grounds for "skip." |
| Moderate negative | -2 | N8 (bulk submission), N9 (bot spam) | Strong patterns of bot-generated PRs, but occasionally appear in legitimate work |
| Weak negative | -1 | N1 (single commit), N2 (no linked issue), N7 (no prior contributions), N10 (template description) | Common in legitimate first-time contributions; only meaningful in combination |
| Weak positive | +1 | P1 (multiple commits), P2 (linked issue), P6 (docs PR), P7 (small diff) | Easy to check, mildly reassuring, but easy to fake |
| Moderate positive | +2 | P3 (contributor track record), P4 (sustained engagement), P8 (substantive discussion) | Hard to fake, indicate real human investment |
| Strong positive | +3 | P5 (evidence of manual testing) | The single strongest indicator that a human actually ran the code |

Raw score = sum of (tier weight * confidence) for all detected signals. Normalize to 1-10 scale with floor/ceiling clamps.

This is explicitly a starting point, not a final model. It lets us ship something usable while we collect data.

**Phase 2: Proxy labels from GitHub history (building the dataset)**

GitHub's PR history provides noisy but abundant proxy labels. For a target repo, we classify historical PRs:

| Outcome | Proxy label | How to extract |
|---------|-------------|----------------|
| Merged after substantive review | **positive** (worth reviewing) | `gh pr list --state merged`, filter for PRs with >= 1 reviewer comment |
| Merged with no review discussion | **weak positive** | Merged but 0 reviewer comments; may be trivial or auto-merged |
| Closed without merge, < 48h, < 3 comments | **negative** (likely slop) | Quick close with minimal discussion suggests obvious rejection |
| Closed without merge, with substantive discussion | **exclude** | Legitimate PRs that were superseded, out of scope, or rejected on design grounds |
| Still open | **exclude** | No outcome yet |

Additional label-refinement heuristics:
- Draft PRs are excluded (often used to save work in progress or trigger CI, not meaningful as review outcomes)
- PRs closed by a bot (e.g., stale-bot) are excluded
- PRs closed by the author themselves are excluded (withdrawn, not rejected)
- PRs with "duplicate" or "wontfix" labels are excluded
- Time-to-close for negative-labeled PRs can be used as a confidence weight (faster close = more obvious slop)

For a repo like vLLM with thousands of closed PRs, this produces a dataset of hundreds to low thousands of labeled examples.

**Script:** `build_dataset.py` fetches historical PRs via `gh api`, extracts the feature vector for each (running the same signal detectors used in live scoring), and assigns proxy labels. Output is a CSV/JSON file suitable for model fitting.

**Phase 3: Logistic regression (learned weights)**

With a labeled dataset from Phase 2, fit a logistic regression to learn signal weights:

- **Input features**: The feature vector from Phase 0 (continuous values where available, booleans otherwise, plus confidence scores)
- **Target**: Binary label (worth reviewing vs. not)
- **Model**: `sklearn.linear_model.LogisticRegression` with L2 regularization
- **Output**: Learned coefficients become the signal weights; the model's predicted probability becomes the readiness score

Why logistic regression specifically:
- **Interpretable**: Each coefficient directly maps to a signal weight, so reviewers can understand and challenge the model ("why does single-commit matter so much in this repo?")
- **Small data friendly**: Works with hundreds of examples, which is realistic for most repos
- **Fast to fit**: No GPU needed, runs in seconds
- **Monotonic in features**: A higher hallucination count always pushes the score down, never up. This matches reviewer intuition and avoids surprising non-linearities.
- **Coefficients are the deliverable**: We don't need to ship sklearn at inference time. The trained coefficients become a weight vector that `score_signals.py` applies as a simple dot product + sigmoid.

If the dataset is large enough (1000+ examples), we can explore gradient-boosted trees for comparison, but interpretability should win ties.

**Feature selection**: After fitting, run a feature selection step to identify signals that are not worth the cost of computing. Some signals are cheap (N1 commit count is a single API call), while others are expensive (N3 hallucinated references requires outbound HTTP requests, N6 unrelated fix requires LLM judgment). Signals that don't improve predictive accuracy enough to justify their extraction cost should be removed from the pipeline entirely. This is a tool-level decision, not a per-repo decision. We run feature selection against our available training data and ship the tool with a fixed set of signals. Per-repo calibration (Phase 4) then learns weights over that fixed set; learned models will naturally downweight signals that are irrelevant for a given repo without requiring users to run their own feature selection.

**Phase 4: Per-repo calibration loop**

Different repos have different norms. A single-commit PR is suspicious in vLLM but normal in a small utility repo. The calibration loop:

1. Run `build_dataset.py` against the target repo's PR history
2. Fit logistic regression on that repo's data
3. Export learned weights to a `.pr-triage.yml` config file in the repo (or a local config)
4. Optionally: run the fitted model against a held-out set and report precision/recall so the user can decide if the model is useful for their repo

This means the Phase 1 expert weights are the defaults, and Phase 3/4 produces per-repo overrides. A repo maintainer doesn't need to run calibration to use the tool, but the tool gets better if they do.

**Phase 5: Feedback loop (optional, future)**

If we add a mechanism for reviewers to flag the tool's assessments as correct or incorrect (e.g., a thumbs-up/down on the output, or tracking whether the reviewer actually reviewed a PR the tool recommended skipping), we can retrain on direct labels rather than proxy labels. This is out of scope for the initial build but the feature vector design should make it straightforward to add later.

#### Output format

The scored output for a single PR:

- **Readiness score**: 1 to 10 (sigmoid of weighted sum, scaled)
- **Recommendation**: Review / Investigate / Skip (thresholded from score; default thresholds: >= 7 Review, 4-6 Investigate, <= 3 Skip). "Investigate" means the signals are mixed: spend 60 seconds looking at the PR description and top signals before deciding whether to do a full review or skip it.
- **Signal breakdown**: Each detected signal with its weight, confidence, evidence, and contribution to the final score
- **Evidence summary**: The top 3 signals by score contribution, with specific cited evidence (e.g., "PR references model `google/gemma-4-27b-it` which does not exist on HuggingFace")
- **Calibration source**: Whether the score used expert defaults or learned weights, and if learned, the training set size and date

### Plugin structure

Following the conventions established by the `rfe-dedup` plugin:

```
agent-plugins/pr-triage/
  .claude-plugin/
    plugin.json                    # Plugin metadata
  agents/
    pr-scorer.md                   # Evaluates one PR against the rubric
    contributor-profiler.md        # Analyzes contributor history and patterns
  skills/
    pr.triage/
      SKILL.md                     # Primary skill: review a single PR
      scripts/
        fetch_pr.py                # Fetch PR metadata, diff, and comments via gh CLI
        fetch_contributor.py       # Fetch contributor history across the repo
        check_references.py        # Verify that referenced artifacts exist
        score_signals.py           # Compute readiness score from signal assessments
      references/
        rubric.md                  # The heuristic rubric (source of truth)
        default_weights.json       # Phase 1 expert-assigned tier weights
    pr.scan/
      SKILL.md                     # Secondary skill: batch score open PRs
      scripts/
        list_open_prs.py           # List open PRs in a repo via gh CLI
        rank_results.py            # Sort and format batch results
    pr.calibrate/
      SKILL.md                     # Calibration skill: fit weights from repo history
      scripts/
        build_dataset.py           # Extract features + proxy labels from historical PRs
        fit_model.py               # Fit logistic regression, export learned weights
        evaluate_model.py          # Precision/recall on held-out set
  tests/
    ...
```

### Skills

#### `pr.triage` (primary)

Invoked as `/pr.triage <PR-URL-or-number>`. Reviews a single PR and produces a scored assessment.

**Workflow:**

1. Fetch PR metadata (title, description, commits, diff, comments, linked issues) via `gh` CLI
2. Fetch contributor profile (merged PR count, open PR count, time span of activity, recent submission rate)
3. Launch `pr-scorer` agent with the PR data and rubric to evaluate heuristic signals
4. If the scorer flags hallucinated references (N3), run `check_references.py` to verify artifacts exist
5. Compute readiness score from signal assessments
6. Output the scored assessment with evidence

**Data sources (all via `gh` CLI):**

- `gh pr view` for PR metadata
- `gh pr diff` for the changeset
- `gh pr checks` for CI status
- `gh api` for commit history, contributor activity, linked issues, and comment threads
- `curl` or `python requests` for verifying external references (HuggingFace model existence, etc.)

#### `pr.scan` (secondary)

Invoked as `/pr.scan <repo> [--limit N] [--label <label>]`. Batch scores open PRs.

**Workflow:**

1. List open PRs in the target repo (with optional filters)
2. For each PR, launch a `pr-scorer` agent in parallel (wave size TBD based on rate limits)
3. Aggregate scores and rank PRs from most to least review-worthy
4. Output a summary table with scores, recommendations, and top signals per PR

### Agents

#### `pr-scorer`

Receives: PR metadata (title, description, commits, diff, comments, linked issues) and the heuristic rubric.

Produces: A JSON assessment with each signal's status (detected / not-detected / inconclusive), confidence, and supporting evidence.

This agent does the qualitative judgment work: reading the PR description for third-person tells, evaluating whether tests are realistic, assessing whether the fix addresses the stated problem.

#### `contributor-profiler`

Receives: A GitHub username and repository.

Produces: A JSON profile with merged PR count, open PR count, first contribution date, most recent contribution, submission rate (PRs per week), and whether the contributor shows a sustained engagement pattern.

### Configuration

The plugin should support per-repo customization of:

- **Signal weights**: Which heuristics matter most for this repo
- **Thresholds**: What score constitutes "review" vs. "investigate" vs. "skip"
- **Disabled signals**: Some repos may not care about certain heuristics

This configuration can be a YAML file in the target repo (e.g., `.pr-triage.yml`) or passed as arguments to the skill.

### What this tool does NOT do

- **It does not write back to GitHub (MVP).** It produces an assessment locally for a human reviewer. It does not add labels, post comments, or modify PRs.
- **It does not replace code review.** It triages whether a PR is worth reviewing, not whether the code is correct.
- **It does not enforce governance policy.** Vouch systems, auto-close rules, and contributor requirements are repo-level decisions outside this tool's scope.
- **It does not guarantee detection.** A sophisticated actor could craft a PR that passes all heuristics. The tool raises the bar, not the ceiling.

### Future directions (out of scope for MVP)

- **GitHub write-back**: Apply triage labels (e.g., `triage:review`, `triage:skip`) or post summary comments on PRs. This would require write scopes on the GitHub token and careful design around who controls the labeling policy. A likely first step would be a `--label` flag on `pr.scan` that applies labels after the reviewer approves the batch results, rather than fully automated labeling.
- **Built-in sandboxing**: Users may want to run this tool in a sandbox, especially as part of a CI job. In future iterations, we could build automatic sandboxing into the tool itself, but that is out of scope for now.

### Security considerations

- **Minimum token scopes**: The MVP requires only read-only GitHub access. The minimum fine-grained PAT scopes are `pull_requests:read`, `issues:read`, `contents:read`, and `metadata:read`. Fine-grained PATs cannot be created from the CLI, but the tool can generate a pre-filled GitHub token creation URL with the correct scopes and open it in the browser, so the user just clicks "Generate token" and pastes the result. Reviewers running locally will typically use their existing `gh` auth instead.
- **External reference checks**: `check_references.py` makes outbound HTTP requests to verify that artifacts referenced in PR descriptions actually exist (e.g., Hugging Face model pages). Since PR descriptions are attacker-controlled input, the script should use HEAD requests and check status codes only. It should never read, log, or report raw response bodies. This is sufficient for existence checks and avoids leaking internal responses through CI logs or future write-back features. The MVP will allow requests to any host by default, but provide a configuration option to restrict outbound checks to a host allowlist for users who want tighter controls. Additionally, the fetch script should enforce basic request hygiene: validate URL schemes (HTTPS only), disallow redirects to private/reserved IP ranges, enforce short connection and read timeouts, and cap response sizes. These checks should live in a shared utility (script or MCP server) rather than in raw `curl` calls, so they apply consistently across all reference verification.

## Status

Proposed

## Consequences

### Positive

- **Saves reviewer time**: Maintainers can quickly identify which PRs deserve attention and which are likely noise, potentially saving hours per day in high-traffic repos
- **Provides evidence, not just opinion**: Each signal comes with specific, cited evidence, so reviewers can quickly verify the assessment rather than taking it on faith
- **Adaptable across repos**: The heuristic rubric is configurable, so different upstream communities can tune it to their specific patterns and norms
- **Reusable as an adversarial quality check**: The same rubric could be integrated into an AI software factory pipeline as a quality gate, similar to a code linter
- **Builds on existing plugin patterns**: Following the rfe-dedup plugin structure means we have a proven template for the implementation

### Negative

- **GitHub API rate limits**: Batch scanning of large repos will hit rate limits; the tool needs to handle this gracefully (e.g., pagination, caching, backoff)
- **False positives risk**: Some heuristics (e.g., single commit, no prior contributions) penalize legitimate first-time contributors; weight tuning and clear documentation are needed to mitigate this
- **Maintenance of reference checks**: Verifying external references (e.g., HuggingFace model existence) depends on external APIs that may change or become unavailable
- **Proxy labels are noisy**: The Phase 2 labeling strategy (merged = good, quickly closed = bad) conflates "not worth reviewing" with "rejected on technical grounds." Calibration results should be reviewed by a domain expert before trusting the learned weights
- **Repo-specific tuning required**: The default expert weights may not work well for every repo; running `pr.calibrate` improves accuracy but requires sufficient PR history (ideally 200+ closed PRs)
- **Scope creep risk**: There will be pressure to expand this into a full code review tool; the spec explicitly limits scope to triage (is this worth reviewing?) rather than review (is this code correct?)
