import json
import pytest
from pathlib import Path

import form_groups


def make_match(rfe_a, rfe_b, degree, **extra):
    base = {
        "rfe_a": rfe_a,
        "rfe_b": rfe_b,
        "match_degree": degree,
        "match_degree_label": {
            1: "None", 2: "Tangential", 3: "Partial", 4: "Substantial", 5: "Duplicate"
        }.get(degree, "Unknown"),
        "overlap_type": "business_need",
        "overlap_description": "Both address similar needs",
        "unique_to_a": "Feature A only",
        "unique_to_b": "Feature B only",
        "merge_feasible": True,
        "merge_concern": None,
        "intentional_decomposition": False,
    }
    base.update(extra)
    return base


def build_lookup(matches):
    return {tuple(sorted([m["rfe_a"], m["rfe_b"]])): m for m in matches}


class TestTruncate:
    def test_short_text_unchanged(self):
        assert form_groups.truncate("hello", 100) == "hello"

    def test_none_returns_empty(self):
        assert form_groups.truncate(None, 100) == ""

    def test_empty_string_unchanged(self):
        assert form_groups.truncate("", 100) == ""

    def test_over_limit_gets_truncated_suffix(self):
        text = "a" * 200
        result = form_groups.truncate(text, 100)
        assert result.endswith("...[truncated]")
        assert len(result) == 100 + len("...[truncated]")


class TestFindConnectedComponents:
    def test_single_pair_forms_one_group(self):
        matches = [make_match("RHAIRFE-1", "RHAIRFE-2", 3)]
        groups = form_groups.find_connected_components(matches)
        assert len(groups) == 1
        assert sorted(groups[0]["members"]) == ["RHAIRFE-1", "RHAIRFE-2"]

    def test_two_disjoint_pairs_form_two_groups(self):
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-3", "RHAIRFE-4", 4),
        ]
        groups = form_groups.find_connected_components(matches)
        assert len(groups) == 2

    def test_chain_a_b_and_b_c_forms_one_group(self):
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-2", "RHAIRFE-3", 3),
        ]
        groups = form_groups.find_connected_components(matches)
        assert len(groups) == 1
        assert sorted(groups[0]["members"]) == ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"]

    def test_empty_matches_returns_empty(self):
        assert form_groups.find_connected_components([]) == []

    def test_groups_sorted_by_size_descending(self):
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-2", "RHAIRFE-3", 3),
            make_match("RHAIRFE-4", "RHAIRFE-5", 3),
        ]
        groups = form_groups.find_connected_components(matches)
        sizes = [len(g["members"]) for g in groups]
        assert sizes == sorted(sizes, reverse=True)

    def test_members_sorted_alphabetically(self):
        matches = [make_match("RHAIRFE-5", "RHAIRFE-1", 3)]
        groups = form_groups.find_connected_components(matches)
        assert groups[0]["members"] == sorted(groups[0]["members"])

    def test_pairwise_matches_populated(self):
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-2", "RHAIRFE-3", 4),
        ]
        groups = form_groups.find_connected_components(matches)
        assert len(groups) == 1
        assert len(groups[0]["pairwise_matches"]) == 2

    def test_pairwise_matches_only_known_pairs(self):
        # Triangle: A-B and A-C but no B-C match recorded.
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-1", "RHAIRFE-3", 3),
        ]
        groups = form_groups.find_connected_components(matches)
        assert len(groups) == 1
        # Only 2 pairs were in matches, not 3.
        assert len(groups[0]["pairwise_matches"]) == 2


class TestBuildAdj:
    def test_includes_edge_at_min_degree(self):
        members = ["A", "B"]
        lookup = {("A", "B"): {"match_degree": 3}}
        adj = form_groups._build_adj(members, lookup, min_degree=3)
        assert "B" in adj["A"]

    def test_excludes_edge_below_min_degree(self):
        members = ["A", "B", "C"]
        lookup = {
            ("A", "B"): {"match_degree": 3},
            ("A", "C"): {"match_degree": 2},  # below threshold
        }
        adj = form_groups._build_adj(members, lookup, min_degree=3)
        assert "B" in adj["A"]
        assert "C" not in adj["A"]

    def test_adjacency_is_bidirectional(self):
        members = ["A", "B"]
        lookup = {("A", "B"): {"match_degree": 4}}
        adj = form_groups._build_adj(members, lookup, min_degree=3)
        assert "B" in adj["A"]
        assert "A" in adj["B"]

    def test_no_edges_if_none_qualify(self):
        members = ["A", "B"]
        lookup = {("A", "B"): {"match_degree": 2}}
        adj = form_groups._build_adj(members, lookup, min_degree=3)
        assert len(adj["A"]) == 0
        assert len(adj["B"]) == 0

    def test_missing_pair_in_lookup_ignored(self):
        members = ["A", "B"]
        adj = form_groups._build_adj(members, {}, min_degree=3)
        assert len(adj["A"]) == 0


class TestBfsComponents:
    def test_single_connected_component(self):
        adj = {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}
        comps = form_groups._bfs_components(["A", "B", "C"], adj)
        assert len(comps) == 1
        assert sorted(comps[0]) == ["A", "B", "C"]

    def test_two_disconnected_components(self):
        adj = {"A": {"B"}, "B": {"A"}, "C": {"D"}, "D": {"C"}}
        comps = form_groups._bfs_components(["A", "B", "C", "D"], adj)
        assert len(comps) == 2

    def test_empty_nodes_returns_empty(self):
        assert form_groups._bfs_components([], {}) == []

    def test_isolated_nodes_each_form_own_component(self):
        comps = form_groups._bfs_components(["A", "B", "C"], {})
        assert len(comps) == 3

    def test_components_sorted(self):
        adj = {"C": {"A"}, "A": {"C"}, "B": {}}
        comps = form_groups._bfs_components(["A", "B", "C"], adj)
        for comp in comps:
            assert comp == sorted(comp)


class TestSplitIncoherentGroups:
    def test_two_member_group_never_split(self):
        matches = [make_match("RHAIRFE-1", "RHAIRFE-2", 2)]
        groups = form_groups.find_connected_components(matches)
        lookup = build_lookup(matches)
        result = form_groups.split_incoherent_groups(groups, lookup, min_degree=3)
        assert len(result) == 1

    def test_coherent_three_member_group_not_split(self):
        # All pairs at degree 4 -> avg = 4.0 >= COHERENCE_THRESHOLD
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 4),
            make_match("RHAIRFE-2", "RHAIRFE-3", 4),
            make_match("RHAIRFE-1", "RHAIRFE-3", 4),
        ]
        groups = form_groups.find_connected_components(matches)
        lookup = build_lookup(matches)
        result = form_groups.split_incoherent_groups(groups, lookup, min_degree=3)
        assert len(result) == 1
        assert len(result[0]["members"]) == 3

    def test_incoherent_group_splits_via_higher_degree(self):
        # Two tight clusters {1,2,3} and {4,5,6} connected by one degree-3 bridge.
        # Many degree-2 cross-cluster pairs drag avg below COHERENCE_THRESHOLD=3.0.
        cluster1 = ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"]
        cluster2 = ["RHAIRFE-4", "RHAIRFE-5", "RHAIRFE-6"]

        matches = []
        # Intra-cluster 1: all degree 4
        for i, a in enumerate(cluster1):
            for b in cluster1[i + 1:]:
                matches.append(make_match(a, b, 4))
        # Intra-cluster 2: all degree 4
        for i, a in enumerate(cluster2):
            for b in cluster2[i + 1:]:
                matches.append(make_match(a, b, 4))
        # Bridge: one degree-3 edge connecting the clusters
        matches.append(make_match("RHAIRFE-2", "RHAIRFE-4", 3))
        # All other cross-cluster pairs evaluated at degree 2
        for a in cluster1:
            for b in cluster2:
                if not (a == "RHAIRFE-2" and b == "RHAIRFE-4"):
                    matches.append(make_match(a, b, 2))

        edge_matches = [m for m in matches if m["match_degree"] >= 3]
        groups = form_groups.find_connected_components(edge_matches)
        assert len(groups) == 1, "Test setup: should form one group at min_degree=3"
        assert len(groups[0]["members"]) == 6

        lookup = build_lookup(matches)
        result = form_groups.split_incoherent_groups(groups, lookup, min_degree=3)

        assert len(result) == 2
        sizes = sorted([len(g["members"]) for g in result], reverse=True)
        assert sizes == [3, 3]

    def test_already_split_groups_not_further_split(self):
        # Two groups already separate; split_incoherent_groups should pass them through.
        matches_g1 = [make_match("RHAIRFE-1", "RHAIRFE-2", 4)]
        matches_g2 = [make_match("RHAIRFE-3", "RHAIRFE-4", 4)]
        groups = [
            {"members": ["RHAIRFE-1", "RHAIRFE-2"], "pairwise_matches": matches_g1},
            {"members": ["RHAIRFE-3", "RHAIRFE-4"], "pairwise_matches": matches_g2},
        ]
        lookup = build_lookup(matches_g1 + matches_g2)
        result = form_groups.split_incoherent_groups(groups, lookup, min_degree=3)
        assert len(result) == 2


class TestWriteGroupsSummary:
    def test_writes_valid_json_file(self, tmp_path):
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-2", "RHAIRFE-3", 4),
        ]
        groups = form_groups.find_connected_components(matches)
        output_path = tmp_path / "groups_summary.json"
        form_groups.write_groups_summary(groups, matches, min_degree=3, output_path=output_path)

        data = json.loads(output_path.read_text())
        assert "metadata" in data
        assert "groups" in data
        assert "cross_group_refs" in data
        assert "ungrouped" in data

    def test_metadata_reflects_inputs(self, tmp_path):
        matches = [make_match("RHAIRFE-1", "RHAIRFE-2", 3)]
        groups = form_groups.find_connected_components(matches)
        output_path = tmp_path / "groups_summary.json"
        form_groups.write_groups_summary(groups, matches, min_degree=3, output_path=output_path)

        data = json.loads(output_path.read_text())
        meta = data["metadata"]
        assert meta["total_rfes_in_matches"] == 2
        assert meta["total_groups"] == 1
        assert meta["min_degree"] == 3
        assert meta["total_confirmed_matches"] == 1

    def test_ungrouped_rfes_identified(self, tmp_path):
        # RHAIRFE-3 appears in a degree-2 match (not forming a group edge).
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-1", "RHAIRFE-3", 2),  # tangential, won't form edge
        ]
        edge_matches = [m for m in matches if m["match_degree"] >= 3]
        groups = form_groups.find_connected_components(edge_matches)
        output_path = tmp_path / "groups_summary.json"
        form_groups.write_groups_summary(groups, matches, min_degree=3, output_path=output_path)

        data = json.loads(output_path.read_text())
        assert "RHAIRFE-3" in data["ungrouped"]

    def test_cross_group_refs_identified(self, tmp_path):
        # Two separate groups, with one cross-group match between them.
        matches = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 4),  # group 1
            make_match("RHAIRFE-3", "RHAIRFE-4", 4),  # group 2
            make_match("RHAIRFE-1", "RHAIRFE-3", 3),  # cross-group reference
        ]
        edge_matches = [matches[0], matches[1]]
        groups = form_groups.find_connected_components(edge_matches)
        output_path = tmp_path / "groups_summary.json"
        form_groups.write_groups_summary(groups, matches, min_degree=3, output_path=output_path)

        data = json.loads(output_path.read_text())
        assert len(data["cross_group_refs"]) == 1
        ref = data["cross_group_refs"][0]
        assert ref["group_a"] != ref["group_b"]

    def test_empty_groups_produces_valid_output(self, tmp_path):
        output_path = tmp_path / "groups_summary.json"
        form_groups.write_groups_summary([], [], min_degree=3, output_path=output_path)
        data = json.loads(output_path.read_text())
        assert data["metadata"]["total_groups"] == 0
        assert data["groups"] == []
        assert data["ungrouped"] == []
