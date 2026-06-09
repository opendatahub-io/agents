#!/usr/bin/env python3
"""Filter candidate pairs that share a Jira link relationship.

Removes pairs where both RFEs belong to the same "link family" —
a connected component in the graph of Split, Duplicate, and Cloners
links. This catches siblings (A split-to B, A split-to C → B and C
are filtered) even when they have no direct link between them.

Overwrites candidates.json in place with the filtered list.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_LINK_TYPES = "Issue split,Duplicate,Cloners"


def build_link_families(rfes_dir, link_types):
    """Build connected components from Jira issue links.

    Returns (key_to_family, stats) where key_to_family maps each
    linked issue key to a frozenset of all keys in its family,
    and stats tracks how many links of each type were found.
    """
    link_type_set = set(link_types)
    adjacency = defaultdict(set)
    type_counts = defaultdict(int)
    files_with_links = 0

    for rfe_file in sorted(rfes_dir.glob("*.json")):
        if rfe_file.name == "_meta.json":
            continue
        issue = json.loads(rfe_file.read_text())
        key = issue["key"]
        has_matching_link = False
        for link in issue.get("links", []):
            if link["type"] in link_type_set:
                adjacency[key].add(link["key"])
                adjacency[link["key"]].add(key)
                type_counts[link["type"]] += 1
                has_matching_link = True
        if has_matching_link:
            files_with_links += 1

    visited = set()
    key_to_family = {}

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

        family_id = frozenset(component)
        for member in component:
            key_to_family[member] = family_id

    families = set(key_to_family.values())
    return key_to_family, len(families), type_counts, files_with_links


def filter_candidates(candidates, key_to_family):
    filtered = []
    removed = 0

    for cand in candidates:
        a_family = key_to_family.get(cand["rfe_a"])
        b_family = key_to_family.get(cand["rfe_b"])
        if a_family is not None and a_family == b_family:
            removed += 1
        else:
            filtered.append(cand)

    return filtered, removed


def main():
    parser = argparse.ArgumentParser(
        description="Filter candidate pairs with Jira link relationships"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates.json (overwritten with filtered result)",
    )
    parser.add_argument(
        "--rfes-dir",
        required=True,
        help="Directory with individual RFE JSON files",
    )
    parser.add_argument(
        "--link-types",
        default=DEFAULT_LINK_TYPES,
        help=f"Comma-separated Jira link type names to filter (default: {DEFAULT_LINK_TYPES})",
    )
    args = parser.parse_args()

    candidates_path = Path(args.candidates)
    rfes_dir = Path(args.rfes_dir)
    link_types = [t.strip() for t in args.link_types.split(",")]

    if not candidates_path.exists():
        print(f"Error: {candidates_path} not found", file=sys.stderr)
        sys.exit(1)
    if not rfes_dir.is_dir():
        print(f"Error: {rfes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    data = json.loads(candidates_path.read_text())
    candidates = data.get("candidates", [])

    key_to_family, num_families, type_counts, files_with_links = build_link_families(
        rfes_dir, link_types
    )

    if files_with_links == 0:
        rfe_count = len(list(rfes_dir.glob("*.json"))) - (1 if (rfes_dir / "_meta.json").exists() else 0)
        if rfe_count > 0:
            print(
                f"Warning: no RFE files contain link data (may be cached from before "
                f"issuelinks were fetched — rerun fetch_rfes.py with --no-cache)",
                file=sys.stderr,
            )
        print(
            f"Filtered 0 candidate pairs (no link data found); "
            f"{len(candidates)} candidates remaining",
            file=sys.stderr,
        )
        return

    filtered, removed = filter_candidates(candidates, key_to_family)

    data["candidates"] = filtered
    data["total_candidates"] = len(filtered)
    data["filtered_by_links"] = removed
    candidates_path.write_text(json.dumps(data, indent=2))

    type_detail = ", ".join(f"{v} {k}" for k, v in sorted(type_counts.items()))
    print(
        f"Found {num_families} link families from {files_with_links} linked RFEs "
        f"({type_detail})",
        file=sys.stderr,
    )
    print(
        f"Filtered {removed} candidate pairs with link relationships; "
        f"{len(filtered)} candidates remaining",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
