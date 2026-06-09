#!/usr/bin/env python3
"""Fetch RFEs from Jira matching a JQL query.

Writes one JSON file per RFE into an rfes/ subdirectory, plus a small
_meta.json for caching. Downstream scripts read only the individual
RFE files they need.

Auth: reads ~/.config/.jira/.config.yml for server/login, and JIRA_API_TOKEN
env var for the API token. Falls back to JIRA_SERVER and JIRA_USER env vars
if the config file is not present.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print(
        "Error: 'requests' package required. Install with: pip install requests",
        file=sys.stderr,
    )
    sys.exit(1)

PAGE_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 2
CACHE_TTL_HOURS = 4
MAX_ISSUES = 5000
SAFE_KEY_RE = re.compile(r"^[A-Z]+-\d+$")


def _load_jira_cli_config():
    config_path = Path.home() / ".config" / ".jira" / ".config.yml"
    if not config_path.exists():
        return None, None
    server = None
    login = None
    for line in config_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("server:"):
            server = line.split(":", 1)[1].strip()
        elif line.startswith("login:"):
            login = line.split(":", 1)[1].strip()
    return server, login


def get_jira_config():
    cli_server, cli_email = _load_jira_cli_config()

    server = os.environ.get("JIRA_SERVER", cli_server)
    email = os.environ.get("JIRA_USER", cli_email)
    token = os.environ.get("JIRA_API_TOKEN")

    missing = []
    if not server:
        missing.append("JIRA_SERVER (or ~/.config/.jira/.config.yml)")
    if not email:
        missing.append("JIRA_USER (or ~/.config/.jira/.config.yml)")
    if not token:
        missing.append("JIRA_API_TOKEN")
    if missing:
        return None, f"Missing Jira config: {', '.join(missing)}"

    if not server.startswith("https://"):
        return None, f"JIRA_SERVER must use HTTPS (got: {server.split('://')[0]}://...)"

    return {"server": server.rstrip("/"), "email": email, "token": token}, None


def api_call_with_retry(url, auth, params=None):
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, auth=auth, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json(), None
            if resp.status_code == 429:
                try:
                    retry_after = int(resp.headers.get("Retry-After", RETRY_DELAY * (attempt + 1)))
                except (ValueError, TypeError):
                    retry_after = RETRY_DELAY * (attempt + 1)
                print(f"Rate limited, waiting {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            return None, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return None, f"Request failed: {e}"
    return None, "Max retries exceeded"


_LUCENE_SPECIALS = r'+-&|!(){}[]^"~*?:\/'


def lucene_escape(text):
    result = text.replace("\\", "\\\\")
    for ch in _LUCENE_SPECIALS:
        if ch != "\\":
            result = result.replace(ch, f"\\{ch}")
    return result


def jql_string_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def adf_to_text(node):
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    text_parts = []
    if node.get("type") == "text":
        return node.get("text", "")
    for child in node.get("content", []):
        text_parts.append(adf_to_text(child))
    joiner = "\n" if node.get("type") in ("doc", "heading", "paragraph", "bulletList", "orderedList", "listItem", "blockquote", "codeBlock", "table", "tableRow") else ""
    return joiner.join(text_parts)


def parse_issue(issue, include_comments):
    fd = issue.get("fields", {})

    comments = []
    if include_comments and "comment" in fd:
        comment_data = fd["comment"]
        if isinstance(comment_data, dict):
            for c in comment_data.get("comments", []):
                body_raw = c.get("body", "")
                body = adf_to_text(body_raw) if isinstance(body_raw, dict) else body_raw
                comments.append(
                    {
                        "author": c.get("author", {}).get("displayName", "Unknown"),
                        "created": c.get("created", ""),
                        "body": body,
                    }
                )

    desc_raw = fd.get("description", "")
    description = adf_to_text(desc_raw) if isinstance(desc_raw, dict) else (desc_raw or "")

    links = []
    for link in fd.get("issuelinks", []):
        link_type = link.get("type", {}).get("name", "")
        if "inwardIssue" in link:
            links.append({
                "type": link_type,
                "direction": "inward",
                "key": link["inwardIssue"]["key"],
            })
        elif "outwardIssue" in link:
            links.append({
                "type": link_type,
                "direction": "outward",
                "key": link["outwardIssue"]["key"],
            })

    return {
        "key": issue["key"],
        "summary": fd.get("summary", ""),
        "description": description,
        "status": (fd.get("status") or {}).get("name", ""),
        "priority": (fd.get("priority") or {}).get("name", ""),
        "components": [c.get("name", "") for c in (fd.get("components") or [])],
        "labels": fd.get("labels") or [],
        "comments": comments,
        "links": links,
    }


def fetch_rfes(jql, config, include_comments=True):
    auth = (config["email"], config["token"])
    base_url = f"{config['server']}/rest/api/3/search/jql"

    fields = [
        "summary",
        "description",
        "status",
        "components",
        "labels",
        "priority",
        "issuetype",
        "issuelinks",
    ]
    if include_comments:
        fields.append("comment")

    all_issues = []
    next_page_token = None
    page = 0

    while True:
        params = {
            "jql": jql,
            "maxResults": PAGE_SIZE,
            "fields": ",".join(fields),
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token

        page += 1
        print(
            f"Fetching page {page} (up to {PAGE_SIZE} issues)...",
            file=sys.stderr,
        )
        data, err = api_call_with_retry(base_url, auth, params)

        if err:
            print(f"Error fetching issues: {err}", file=sys.stderr)
            sys.exit(1)

        issues = data.get("issues", [])
        if not issues:
            break

        for issue in issues:
            all_issues.append(parse_issue(issue, include_comments))

        if len(all_issues) >= MAX_ISSUES:
            print(
                f"Error: fetched {len(all_issues)} issues, exceeding MAX_ISSUES={MAX_ISSUES}. "
                "Narrow your JQL scope.",
                file=sys.stderr,
            )
            sys.exit(1)

        if data.get("isLast", False) or not data.get("nextPageToken"):
            break
        next_page_token = data["nextPageToken"]

    print(f"Fetched {len(all_issues)} issues", file=sys.stderr)
    return all_issues


def load_cache(meta_path, jql):
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if meta.get("jql") != jql:
        return None
    age_hours = (time.time() - meta.get("fetched_at", 0)) / 3600
    if age_hours > CACHE_TTL_HOURS:
        return None
    return meta


def main():
    parser = argparse.ArgumentParser(description="Fetch RFEs from Jira")
    parser.add_argument("--jql", required=True, help="JQL query to execute")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for output (rfes/ subdirectory created here)",
    )
    parser.add_argument(
        "--no-comments", action="store_true", help="Skip fetching comments"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Skip cache, always fetch fresh"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    rfes_dir = output_dir / "rfes"
    meta_path = rfes_dir / "_meta.json"

    if not args.no_cache:
        meta = load_cache(meta_path, args.jql)
        if meta:
            age = (time.time() - meta["fetched_at"]) / 3600
            print(
                f"Using cached results ({age:.1f}h old, {meta['total']} issues)",
                file=sys.stderr,
            )
            return

    config, err = get_jira_config()
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    issues = fetch_rfes(args.jql, config, include_comments=not args.no_comments)

    rfes_dir.mkdir(parents=True, exist_ok=True)

    for issue in issues:
        if not SAFE_KEY_RE.match(issue["key"]):
            print(f"Warning: skipping issue with unsafe key: {issue['key']!r}", file=sys.stderr)
            continue
        issue_path = rfes_dir / f"{issue['key']}.json"
        issue_path.write_text(json.dumps(issue, indent=2))

    meta = {
        "jql": args.jql,
        "fetched_at": time.time(),
        "server": config["server"],
        "total": len(issues),
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"Wrote {len(issues)} RFE files to {rfes_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
