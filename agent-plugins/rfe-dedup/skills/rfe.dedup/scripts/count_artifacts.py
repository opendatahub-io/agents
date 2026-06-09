#!/usr/bin/env python3
"""Count files in a directory. Prints the count to stdout."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Count files in a directory")
    parser.add_argument("--dir", required=True, help="Directory to count files in")
    args = parser.parse_args()

    target = Path(args.dir)
    if not target.is_dir():
        print(f"Error: {target} is not a directory", file=sys.stderr)
        sys.exit(1)

    count = sum(1 for f in target.iterdir() if f.is_file())
    print(count)


if __name__ == "__main__":
    main()
