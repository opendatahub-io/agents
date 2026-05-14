#!/usr/bin/env python3
"""Assemble the final duplicate analysis report from individual group reports.

Reads report section files from the reports directory and concatenates
them with a header into a single markdown report.

Also reads companion report JSON files and groups_summary.json to
produce a structured dedup_summary.json alongside the markdown report.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Assemble final dedup report from group report sections"
    )
    parser.add_argument(
        "--reports-dir",
        required=True,
        help="Directory containing report_*.md files",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the assembled report",
    )
    parser.add_argument(
        "--groups-summary",
        default=None,
        help="Path to groups_summary.json (optional)",
    )
    parser.add_argument("--jql", required=True, help="JQL query used")
    parser.add_argument("--date", required=True, help="Analysis date")
    parser.add_argument(
        "--rfe-count", required=True, type=int, help="Number of RFEs analyzed"
    )
    parser.add_argument(
        "--group-count", required=True, type=int, help="Number of groups found"
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_dir():
        print(f"Error: {reports_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    report_files = sorted(reports_dir.glob("report_*.md"))
    if not report_files:
        print(f"Error: no report_*.md files in {reports_dir}", file=sys.stderr)
        sys.exit(1)

    header = (
        f"# RFE Duplicate Analysis Report\n\n"
        f"**Query:** {args.jql}\n"
        f"**Date:** {args.date}\n"
        f"**RFEs analyzed:** {args.rfe_count}\n"
        f"**Groups found:** {args.group_count}\n\n"
        f"---\n\n"
    )

    sections = []
    for report_file in report_files:
        sections.append(report_file.read_text(encoding="utf-8"))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(header + "\n".join(sections), encoding="utf-8")

    group_reports = []
    missing_json = 0
    for report_file in report_files:
        json_path = report_file.with_suffix(".json")
        if json_path.exists():
            try:
                group_reports.append(json.loads(json_path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: skipping unreadable {json_path}: {e}",
                    file=sys.stderr,
                )
                missing_json += 1
        else:
            missing_json += 1

    groups_summary_data = None
    if args.groups_summary:
        gs_path = Path(args.groups_summary)
        if gs_path.exists():
            try:
                groups_summary_data = json.loads(gs_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: could not read {gs_path}: {e}",
                    file=sys.stderr,
                )

    if group_reports or groups_summary_data:
        summary = {
            "metadata": {
                "jql": args.jql,
                "date": args.date,
                "rfe_count": args.rfe_count,
                "group_count": args.group_count,
            },
        }
        if groups_summary_data:
            summary["groups_summary"] = groups_summary_data
        if group_reports:
            summary["group_reports"] = group_reports

        json_output = output_path.with_suffix(".json")
        json_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        json_note = f" and {json_output}"
    else:
        json_note = ""

    if missing_json:
        print(
            f"Warning: {missing_json} report JSON files missing or unreadable",
            file=sys.stderr,
        )

    print(
        f"Assembled {len(sections)} group sections into {output_path}{json_note}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
