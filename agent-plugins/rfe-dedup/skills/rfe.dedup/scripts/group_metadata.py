#!/usr/bin/env python3
"""Print metadata for each group file: group number and member count.

Output is TSV lines: <group_num>\t<member_count>
"""

import argparse
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Print group number and member count for each group file"
    )
    parser.add_argument(
        "--groups-dir", required=True, help="Directory containing group_*.md files"
    )
    args = parser.parse_args()

    groups_dir = Path(args.groups_dir)
    if not groups_dir.is_dir():
        print(f"Error: {groups_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    group_files = sorted(groups_dir.glob("group_*.md"))
    if not group_files:
        print("No group files found", file=sys.stderr)
        sys.exit(1)

    for gf in group_files:
        num_match = re.search(r"group_(\d+)\.md$", gf.name)
        if not num_match:
            continue
        group_num = int(num_match.group(1))
        content = gf.read_text()
        member_count = len(re.findall(r"^### [A-Z]+-\d+:", content, re.MULTILINE))
        print(f"{group_num}\t{member_count}")


if __name__ == "__main__":
    main()
