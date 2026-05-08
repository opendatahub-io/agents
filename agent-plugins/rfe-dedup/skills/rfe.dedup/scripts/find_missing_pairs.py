#!/usr/bin/env python3
"""Find and prepare missing intra-group pairwise evaluations.

After groups are formed from confirmed matches, some intra-group pairs
may not have been evaluated (due to candidate truncation or threshold
filtering). This script identifies those gaps and prepares pair files
for a follow-up evaluation pass.

Groups are formed using only matches at or above --min-degree, matching
the threshold used by form_groups.py.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

MAX_DESC_CHARS = 2000
MAX_COMMENT_CHARS = 500
MAX_COMMENTS = 3


def truncate(text, limit):
    if not text or len(text) <= limit:
        return text or ""
    return text[:limit] + "...[truncated]"


def find_connected_components(matches):
    adjacency = defaultdict(set)
    for m in matches:
        a, b = m["rfe_a"], m["rfe_b"]
        adjacency[a].add(b)
        adjacency[b].add(a)

    visited = set()
    groups = []
    for node in adjacency:
        if node in visited:
            continue
        component = []
        queue = [node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        component.sort()
        groups.append(component)

    groups.sort(key=len, reverse=True)
    return groups


def scan_evaluated_pairs(match_dir):
    """Scan match result files to find all pairs that were evaluated,
    including those filtered out at degree < 2."""
    evaluated = set()
    if not match_dir.is_dir():
        return evaluated
    for f in match_dir.glob("match_*.json"):
        try:
            data = json.loads(f.read_text())
            if "rfe_a" in data and "rfe_b" in data:
                pair_key = tuple(sorted([data["rfe_a"], data["rfe_b"]]))
                evaluated.add(pair_key)
        except (json.JSONDecodeError, OSError):
            pass
    return evaluated


def format_pair_markdown(rfe_a, rfe_b, index, total):
    lines = [
        f"## Pair {index}/{total} — gap fill (intra-group)",
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
        description="Find and prepare missing intra-group pair evaluations"
    )
    parser.add_argument(
        "--confirmed-matches",
        required=True,
        help="Path to confirmed_matches.json",
    )
    parser.add_argument(
        "--rfes-dir",
        required=True,
        help="Directory with individual RFE JSON files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Run directory (gap_pairs/ and gap_match_results/ created here)",
    )
    parser.add_argument(
        "--match-dir",
        default=None,
        help="Directory with match_*.json files from initial evaluation "
        "(to detect pairs evaluated at degree < 2). Defaults to <output-dir>/match_results",
    )
    parser.add_argument(
        "--min-degree",
        type=int,
        default=3,
        help="Minimum match degree for group edges (default: 3). "
        "Must match the threshold used by form_groups.py.",
    )
    args = parser.parse_args()

    confirmed_path = Path(args.confirmed_matches)
    rfes_dir = Path(args.rfes_dir)
    output_dir = Path(args.output_dir)
    match_dir = Path(args.match_dir) if args.match_dir else output_dir / "match_results"

    if not confirmed_path.exists():
        print(f"Error: {confirmed_path} not found", file=sys.stderr)
        sys.exit(1)
    if not rfes_dir.is_dir():
        print(f"Error: {rfes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    data = json.loads(confirmed_path.read_text())
    matches = data if isinstance(data, list) else data.get("matches", [])

    edge_matches = [
        m for m in matches
        if m.get("match_degree", 0) >= args.min_degree
    ]
    groups = find_connected_components(edge_matches)

    confirmed_pairs = set()
    for m in matches:
        confirmed_pairs.add(tuple(sorted([m["rfe_a"], m["rfe_b"]])))

    evaluated_pairs = scan_evaluated_pairs(match_dir)

    missing = []
    groups_with_gaps = 0
    for component in groups:
        group_missing = []
        for i, a in enumerate(component):
            for b in component[i + 1 :]:
                pair_key = tuple(sorted([a, b]))
                if pair_key not in confirmed_pairs and pair_key not in evaluated_pairs:
                    group_missing.append(pair_key)
        if group_missing:
            groups_with_gaps += 1
            missing.extend(group_missing)

    if not missing:
        print(
            "No missing intra-group pairs found; all pairs already evaluated",
            file=sys.stderr,
        )
        return

    gap_pairs_dir = output_dir / "gap_pairs"
    gap_pairs_dir.mkdir(parents=True, exist_ok=True)
    gap_results_dir = output_dir / "gap_match_results"
    gap_results_dir.mkdir(parents=True, exist_ok=True)

    total = len(missing)
    written = 0
    for i, (key_a, key_b) in enumerate(missing, 1):
        rfe_a_path = rfes_dir / f"{key_a}.json"
        rfe_b_path = rfes_dir / f"{key_b}.json"

        if not rfe_a_path.exists() or not rfe_b_path.exists():
            skipped = key_a if not rfe_a_path.exists() else key_b
            print(
                f"Warning: {skipped} not found in {rfes_dir}/, skipping pair",
                file=sys.stderr,
            )
            continue

        rfe_a = json.loads(rfe_a_path.read_text())
        rfe_b = json.loads(rfe_b_path.read_text())

        md = format_pair_markdown(rfe_a, rfe_b, i, total)
        pair_path = gap_pairs_dir / f"pair_{i:03d}.md"
        pair_path.write_text(md)
        written += 1

    print(
        f"Found {total} missing intra-group pairs across {groups_with_gaps} groups; "
        f"wrote {written} pair files to {gap_pairs_dir}/",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
