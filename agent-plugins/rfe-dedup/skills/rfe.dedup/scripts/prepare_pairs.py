#!/usr/bin/env python3
"""Prepare candidate pairs for LLM evaluation.

Takes candidates.json and reads individual RFE files from rfes/ to
produce one markdown file per pair in a pairs/ subdirectory. Each file
is ready to be passed directly to an eval-pair agent.
"""

import argparse
import json
import sys
from pathlib import Path

MAX_DESC_CHARS = 2000
MAX_COMMENT_CHARS = 500
MAX_COMMENTS = 3


def truncate(text, limit):
    if not text or len(text) <= limit:
        return text or ""
    return text[:limit] + "...[truncated]"


def load_rfe(rfes_dir, key):
    rfe_path = rfes_dir / f"{key}.json"
    if not rfe_path.exists():
        return None
    return json.loads(rfe_path.read_text())


def format_pair_markdown(rfe_a, rfe_b, similarity, index, total):
    lines = [
        f"## Pair {index}/{total} — similarity {similarity}",
        "",
        f"### A: {rfe_a['key']} — {rfe_a.get('summary', '(no summary)')}",
        "",
    ]

    desc_a = truncate(rfe_a.get("description", ""), MAX_DESC_CHARS)
    if desc_a:
        lines.append(desc_a)
        lines.append("")

    for c in list(reversed(rfe_a.get("comments") or []))[:MAX_COMMENTS]:
        body = truncate(c.get("body", ""), MAX_COMMENT_CHARS)
        if body:
            lines.append(f"> Comment: {body}")
            lines.append("")

    lines.append(f"### B: {rfe_b['key']} — {rfe_b.get('summary', '(no summary)')}")
    lines.append("")

    desc_b = truncate(rfe_b.get("description", ""), MAX_DESC_CHARS)
    if desc_b:
        lines.append(desc_b)
        lines.append("")

    for c in list(reversed(rfe_b.get("comments") or []))[:MAX_COMMENTS]:
        body = truncate(c.get("body", ""), MAX_COMMENT_CHARS)
        if body:
            lines.append(f"> Comment: {body}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare candidate pairs for LLM evaluation"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="JSON file with candidate pairs (from find_candidates.py)",
    )
    parser.add_argument(
        "--rfes-dir",
        required=True,
        help="Directory with individual RFE JSON files (from fetch_rfes.py)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for output (pairs/ subdirectory created here)",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=None,
        help="Max candidate pairs to prepare (default: all)",
    )
    args = parser.parse_args()

    candidates_path = Path(args.candidates)
    rfes_dir = Path(args.rfes_dir)
    output_dir = Path(args.output_dir)

    if not candidates_path.exists():
        print(f"Error: {candidates_path} not found", file=sys.stderr)
        sys.exit(1)
    if not rfes_dir.is_dir():
        print(f"Error: {rfes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    candidates_data = json.loads(candidates_path.read_text())
    candidate_list = candidates_data.get("candidates", [])
    total_available = len(candidate_list)

    if args.max_pairs and args.max_pairs < total_available:
        candidate_list = candidate_list[: args.max_pairs]
        print(
            f"Preparing {args.max_pairs} of {total_available} candidate pairs",
            file=sys.stderr,
        )
    else:
        print(
            f"Preparing all {total_available} candidate pairs",
            file=sys.stderr,
        )

    pairs_dir = output_dir / "pairs"
    pairs_dir.mkdir(parents=True, exist_ok=True)

    match_results_dir = output_dir / "match_results"
    match_results_dir.mkdir(parents=True, exist_ok=True)

    total = len(candidate_list)
    written = 0
    for i, cand in enumerate(candidate_list, 1):
        rfe_a = load_rfe(rfes_dir, cand["rfe_a"])
        rfe_b = load_rfe(rfes_dir, cand["rfe_b"])

        if not rfe_a or not rfe_b:
            missing = cand["rfe_a"] if not rfe_a else cand["rfe_b"]
            print(f"Warning: {missing} not found in {rfes_dir}/, skipping pair", file=sys.stderr)
            continue

        md = format_pair_markdown(rfe_a, rfe_b, cand["similarity_score"], i, total)
        pair_path = pairs_dir / f"pair_{i:03d}.md"
        pair_path.write_text(md)
        written += 1

    print(f"Wrote {written} pair files to {pairs_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
