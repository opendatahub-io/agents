#!/usr/bin/env python3
"""Merge individual match result files into a single confirmed_matches.json.

Reads match_*.json files from the match results directory, combines them
into a list, and writes the merged output.
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Merge individual match result files"
    )
    parser.add_argument(
        "--match-dir",
        required=True,
        help="Directory containing match_*.json files",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for merged confirmed_matches.json",
    )
    args = parser.parse_args()

    match_dir = Path(args.match_dir)
    if not match_dir.is_dir():
        print(f"Error: {match_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    match_files = sorted(glob.glob(str(match_dir / "match_*.json")))

    if not match_files:
        print(
            f"Error: no match_*.json files found in {match_dir}. "
            "Run the eval-pair step before merging.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Detect gaps in the expected sequence (match_001, match_002, ...)
    found_numbers = set()
    for f in match_files:
        name = Path(f).stem  # e.g. "match_042"
        try:
            found_numbers.add(int(name.split("_")[1]))
        except (IndexError, ValueError):
            pass
    if found_numbers:
        expected = set(range(1, max(found_numbers) + 1))
        missing = sorted(expected - found_numbers)
        if missing:
            labels = ", ".join(str(n) for n in missing[:20])
            suffix = f" (and {len(missing) - 20} more)" if len(missing) > 20 else ""
            print(
                f"Warning: {len(missing)} missing match files: {labels}{suffix}",
                file=sys.stderr,
            )

    all_results = []
    skipped_malformed = 0
    for f in match_files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            if not isinstance(data, dict) or "match_degree" not in data:
                print(f"Warning: skipping malformed file {f}", file=sys.stderr)
                skipped_malformed += 1
                continue
            all_results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping unreadable file {f}: {e}", file=sys.stderr)
            skipped_malformed += 1

    confirmed = [
        m for m in all_results
        if isinstance(m.get("match_degree"), (int, float)) and m["match_degree"] >= 2
    ]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(confirmed, indent=2))

    print(
        f"Merged {len(confirmed)} confirmed matches into {output_path} "
        f"({len(all_results)} total evaluated, "
        f"{len(all_results) - len(confirmed)} filtered as degree 1 (no overlap)"
        f"{f', {skipped_malformed} malformed/unreadable' if skipped_malformed else ''})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
