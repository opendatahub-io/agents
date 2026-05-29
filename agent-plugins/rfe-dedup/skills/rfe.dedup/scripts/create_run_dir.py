#!/usr/bin/env python3
"""Create a run directory for an RFE dedup analysis.

Accepts a short human description of the run, normalizes it to a
lowercase hyphen-separated slug, prepends "dedup-", handles collisions
by appending numeric suffixes, creates the directory, and prints the
path to stdout.

The caller (skill) is responsible for coming up with the description;
this script only normalizes and ensures uniqueness.
"""

import argparse
import re
import sys
from pathlib import Path

BASE_DIR = Path(".local")


def normalize_name(name):
    """Normalize a human description to a lowercase hyphen-separated slug.

    Lowercases, replaces any run of non-alphanumeric characters with a
    single hyphen, strips leading/trailing hyphens, and prepends "dedup-".
    """
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '-', name)
    name = name.strip('-')
    return f"dedup-{name}"


def main():
    parser = argparse.ArgumentParser(
        description="Create a uniquely-named run directory for dedup analysis"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Short human description of this analysis run (e.g. 'new rhairfe rfes')",
    )
    args = parser.parse_args()

    name = normalize_name(args.name)

    candidate = BASE_DIR / name
    try:
        candidate.mkdir(parents=True)
        print(candidate)
        return
    except FileExistsError:
        pass

    suffix = 1
    while True:
        candidate = BASE_DIR / f"{name}-{suffix}"
        try:
            candidate.mkdir(parents=True)
            print(candidate)
            return
        except FileExistsError:
            suffix += 1


if __name__ == "__main__":
    main()
