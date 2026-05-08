#!/usr/bin/env python3
"""Form groups of related RFEs from confirmed pairwise matches.

Takes confirmed pairwise matches and finds connected components —
if A matches B and B matches C, then {A, B, C} form a group.
Only matches at or above --min-degree form graph edges, but all
confirmed matches (degree 2+) are included as context in group files.

Reads individual RFE files from rfes/ to produce one markdown file
per group in a groups/ subdirectory. Each file is ready to be passed
directly to a report-group agent.

Also writes groups_summary.json with structured group metadata,
cross-group references, and ungrouped RFEs.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

MAX_DESC_CHARS = 2000
MAX_COMMENT_CHARS = 500
MAX_COMMENTS = 3

# Groups whose average intra-group match degree (over evaluated pairs) falls
# below this value are split by re-running BFS at a higher min-degree. This
# catches transitive over-grouping where sub-clusters are bridged only by
# degree-2 (Tangential) edges.
COHERENCE_THRESHOLD = 3.0


def truncate(text, limit):
    if not text or len(text) <= limit:
        return text or ""
    return text[:limit] + "...[truncated]"


def find_connected_components(matches):
    adjacency = defaultdict(set)
    match_lookup = {}

    for m in matches:
        a, b = m["rfe_a"], m["rfe_b"]
        adjacency[a].add(b)
        adjacency[b].add(a)
        pair_key = tuple(sorted([a, b]))
        match_lookup[pair_key] = m

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
        pairwise = []
        for i, a in enumerate(component):
            for b in component[i + 1:]:
                pair_key = tuple(sorted([a, b]))
                if pair_key in match_lookup:
                    pairwise.append(match_lookup[pair_key])
        groups.append({"members": component, "pairwise_matches": pairwise})

    groups.sort(key=lambda g: len(g["members"]), reverse=True)
    return groups


def _build_adj(members, all_match_lookup, min_degree):
    adj = defaultdict(set)
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            pk = tuple(sorted([a, b]))
            if pk in all_match_lookup and all_match_lookup[pk].get("match_degree", 0) >= min_degree:
                adj[a].add(b)
                adj[b].add(a)
    return adj


def _bfs_components(nodes, adj):
    visited = set()
    comps = []
    for start in nodes:
        if start in visited:
            continue
        comp = []
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            comp.append(curr)
            for nb in adj.get(curr, set()):
                if nb not in visited:
                    queue.append(nb)
        comps.append(sorted(comp))
    return comps


def _try_articulation_split(members, all_match_lookup, min_degree):
    """Find the first articulation point and split the group there.

    Returns a list of member lists (sub-groups) or None if no split found.
    The articulation point is assigned to the component it is most connected
    to (by count then by average degree). Singletons are omitted and will
    surface as ungrouped in the summary.
    """
    adj = _build_adj(members, all_match_lookup, min_degree)

    for cut in sorted(members):
        remaining = [m for m in members if m != cut]
        # Temporarily remove cut from its neighbors' adjacency lists
        for nb in list(adj[cut]):
            adj[nb].discard(cut)

        comps = _bfs_components(remaining, adj)

        # Restore cut in its neighbors' adjacency lists
        for nb in adj[cut]:
            adj[nb].add(cut)

        if len(comps) <= 1:
            continue

        # cut is an articulation point — assign it to the component with the
        # most connections to it, breaking ties by average degree.
        def score(comp):
            degrees = [
                all_match_lookup[tuple(sorted([cut, m]))]["match_degree"]
                for m in comp
                if tuple(sorted([cut, m])) in all_match_lookup
            ]
            return (sum(degrees) / len(degrees) if degrees else 0, len(degrees))

        best_idx = max(range(len(comps)), key=lambda i: score(comps[i]))
        comps[best_idx] = sorted(comps[best_idx] + [cut])
        return [c for c in comps if len(c) >= 2]

    return None


def split_incoherent_groups(groups, all_match_lookup, min_degree):
    """Split groups whose evaluated intra-group pairs average below COHERENCE_THRESHOLD.

    First attempts to split by raising the min-degree threshold. If all edges
    are at the current min-degree (no higher-degree edges exist), falls back to
    articulation point detection — finding a hub node whose removal disconnects
    the group into tighter sub-clusters. Recurses until all sub-groups are
    coherent or cannot be split further.
    """
    result = []
    for group in groups:
        members = group["members"]

        if len(members) < 3:
            result.append(group)
            continue

        # Average over ALL evaluated intra-group pairs (degree 2+) so that
        # degree-2 tangential pairs dragging coherence down are visible.
        all_intra = []
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                pk = tuple(sorted([a, b]))
                if pk in all_match_lookup:
                    all_intra.append(all_match_lookup[pk]["match_degree"])

        avg_degree = sum(all_intra) / len(all_intra) if all_intra else 0.0

        if avg_degree >= COHERENCE_THRESHOLD:
            result.append(group)
            continue

        # --- Strategy 1: raise min-degree and re-cluster ---
        higher_min = min_degree + 1
        higher_edges = [
            all_match_lookup[tuple(sorted([a, b]))]
            for i, a in enumerate(members)
            for b in members[i + 1:]
            if tuple(sorted([a, b])) in all_match_lookup
            and all_match_lookup[tuple(sorted([a, b]))].get("match_degree", 0) >= higher_min
        ]

        if higher_edges:
            sub_groups = find_connected_components(higher_edges)
            reached = {m for sg in sub_groups for m in sg["members"]}
            if len(sub_groups) > 1 or len(reached) < len(members):
                print(
                    f"  Split {len(members)}-member group (avg degree {avg_degree:.2f}) "
                    f"into {len(sub_groups)} sub-group(s) at min-degree {higher_min}",
                    file=sys.stderr,
                )
                for sg in sub_groups:
                    enriched = []
                    for i, a in enumerate(sg["members"]):
                        for b in sg["members"][i + 1:]:
                            pk = tuple(sorted([a, b]))
                            if pk in all_match_lookup:
                                enriched.append(all_match_lookup[pk])
                    sg["pairwise_matches"] = enriched
                result.extend(split_incoherent_groups(sub_groups, all_match_lookup, higher_min))
                continue

        # --- Strategy 2: articulation point detection ---
        sub_member_lists = _try_articulation_split(members, all_match_lookup, min_degree)
        if sub_member_lists and len(sub_member_lists) > 1:
            print(
                f"  Split {len(members)}-member group (avg degree {avg_degree:.2f}) "
                f"into {len(sub_member_lists)} sub-group(s) via articulation point",
                file=sys.stderr,
            )
            sub_groups = []
            for sub_members in sub_member_lists:
                enriched = []
                for i, a in enumerate(sub_members):
                    for b in sub_members[i + 1:]:
                        pk = tuple(sorted([a, b]))
                        if pk in all_match_lookup:
                            enriched.append(all_match_lookup[pk])
                sub_groups.append({"members": sub_members, "pairwise_matches": enriched})
            result.extend(split_incoherent_groups(sub_groups, all_match_lookup, min_degree))
            continue

        # Cannot split further — keep as-is
        result.append(group)

    return result


def load_rfe(rfes_dir, key):
    rfe_path = rfes_dir / f"{key}.json"
    if not rfe_path.exists():
        return None
    return json.loads(rfe_path.read_text())


def format_member(issue):
    lines = [
        f"### {issue['key']}: {issue.get('summary', '(no summary)')}",
        f"- **Priority:** {issue.get('priority', 'Unknown')}",
        f"- **Components:** {', '.join(issue.get('components', [])) or 'None'}",
    ]

    desc = issue.get("description", "")
    if desc:
        lines.append(f"- **Description excerpt:** {truncate(desc, MAX_DESC_CHARS)}")

    comments = issue.get("comments", [])
    if comments:
        for c in list(reversed(comments))[:MAX_COMMENTS]:
            body = truncate(c.get("body", ""), MAX_COMMENT_CHARS)
            if body:
                lines.append(f"\n> Comment: {body}")

    return "\n".join(lines)


def format_pairwise(match):
    lines = [
        f"#### {match['rfe_a']} vs {match['rfe_b']}: "
        f"match_degree {match['match_degree']} ({match.get('match_degree_label', '?')})",
        f"- **Overlap type:** {match.get('overlap_type', 'unknown')}",
        f"- **Overlap:** {match.get('overlap_description', '')}",
        f"- **Unique to {match['rfe_a']}:** {match.get('unique_to_a', '')}",
        f"- **Unique to {match['rfe_b']}:** {match.get('unique_to_b', '')}",
        f"- **Merge feasible:** {match.get('merge_feasible', 'unknown')}",
    ]
    concern = match.get("merge_concern")
    if concern:
        lines.append(f"- **Merge concern:** {concern}")
    if match.get("intentional_decomposition"):
        lines.append("- **Intentional decomposition:** yes")
    return "\n".join(lines)


def write_group_file(group, rfes_dir, output_path):
    members = group["members"]
    pairwise = group["pairwise_matches"]

    member_lines = []
    for key in members:
        issue = load_rfe(rfes_dir, key)
        if issue:
            member_lines.append(format_member(issue))
        else:
            member_lines.append(f"### {key}: (not found in {rfes_dir}/)")

    pairwise_lines = []
    for match in pairwise:
        pairwise_lines.append(format_pairwise(match))

    content = "\n\n".join(member_lines)
    content += "\n\n" + "\n\n".join(pairwise_lines)

    output_path.write_text(content)


def write_groups_summary(groups, all_matches, min_degree, output_path):
    rfe_to_group = {}
    for i, group in enumerate(groups, 1):
        for member in group["members"]:
            rfe_to_group[member] = i

    all_rfes_in_matches = set()
    for m in all_matches:
        all_rfes_in_matches.add(m["rfe_a"])
        all_rfes_in_matches.add(m["rfe_b"])

    grouped_rfes = set(rfe_to_group.keys())
    ungrouped = sorted(all_rfes_in_matches - grouped_rfes)

    cross_group_refs = []
    for m in all_matches:
        a, b = m["rfe_a"], m["rfe_b"]
        ga = rfe_to_group.get(a)
        gb = rfe_to_group.get(b)
        if ga is not None and gb is not None and ga != gb:
            cross_group_refs.append({
                "rfe_a": a,
                "rfe_b": b,
                "match_degree": m["match_degree"],
                "match_degree_label": m.get("match_degree_label", ""),
                "overlap_type": m.get("overlap_type"),
                "group_a": ga,
                "group_b": gb,
            })

    group_entries = []
    for i, group in enumerate(groups, 1):
        edge_count = sum(
            1 for m in group["pairwise_matches"]
            if m.get("match_degree", 0) >= min_degree
        )
        group_entries.append({
            "group_number": i,
            "members": group["members"],
            "edge_count": edge_count,
        })

    summary = {
        "metadata": {
            "total_rfes_in_matches": len(all_rfes_in_matches),
            "total_groups": len(groups),
            "min_degree": min_degree,
            "total_confirmed_matches": len(all_matches),
        },
        "groups": group_entries,
        "cross_group_refs": cross_group_refs,
        "ungrouped": ungrouped,
    }

    output_path.write_text(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Form groups from confirmed pairwise matches"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON file with confirmed pairwise matches",
    )
    parser.add_argument(
        "--rfes-dir",
        required=True,
        help="Directory with individual RFE JSON files (from fetch_rfes.py)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for output (groups/ subdirectory created here)",
    )
    parser.add_argument(
        "--min-degree",
        type=int,
        default=3,
        help="Minimum match degree to form group edges (default: 3)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    rfes_dir = Path(args.rfes_dir)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)
    if not rfes_dir.is_dir():
        print(f"Error: {rfes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text())
    all_matches = data if isinstance(data, list) else data.get("matches", [])

    edge_matches = [
        m for m in all_matches
        if m.get("match_degree", 0) >= args.min_degree
    ]
    groups = find_connected_components(edge_matches)

    all_match_lookup = {}
    for m in all_matches:
        pair_key = tuple(sorted([m["rfe_a"], m["rfe_b"]]))
        all_match_lookup[pair_key] = m

    groups = split_incoherent_groups(groups, all_match_lookup, args.min_degree)

    for group in groups:
        enriched = []
        members = group["members"]
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                pair_key = tuple(sorted([a, b]))
                if pair_key in all_match_lookup:
                    enriched.append(all_match_lookup[pair_key])
        group["pairwise_matches"] = enriched

    groups_dir = output_dir / "groups"
    groups_dir.mkdir(parents=True, exist_ok=True)

    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    for i, group in enumerate(groups, 1):
        group_path = groups_dir / f"group_{i:02d}.md"
        write_group_file(group, rfes_dir, group_path)

    summary_path = output_dir / "groups_summary.json"
    write_groups_summary(groups, all_matches, args.min_degree, summary_path)

    all_grouped = {m for g in groups for m in g["members"]}
    print(
        f"Formed {len(groups)} groups ({len(all_grouped)} RFEs) "
        f"from {len(edge_matches)} edges (min degree {args.min_degree}) "
        f"out of {len(all_matches)} total matches "
        f"-- wrote to {groups_dir}/ and {summary_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
