import json
import pytest
from pathlib import Path

import filter_candidates


def make_rfe(key, links=None):
    return {
        "key": key,
        "summary": f"Summary for {key}",
        "description": "",
        "status": "New",
        "priority": "Major",
        "components": [],
        "labels": [],
        "comments": [],
        "links": links or [],
    }


def make_candidate(rfe_a, rfe_b, score=0.9):
    return {"rfe_a": rfe_a, "rfe_b": rfe_b, "similarity_score": score}


class TestBuildLinkFamilies:
    def test_no_links_returns_empty_family_map(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        for key in ["RHAIRFE-1", "RHAIRFE-2"]:
            (rfes_dir / f"{key}.json").write_text(json.dumps(make_rfe(key)))

        key_to_family, num_families, type_counts, files_with_links = (
            filter_candidates.build_link_families(rfes_dir, ["Issue split", "Duplicate"])
        )
        assert key_to_family == {}
        assert num_families == 0
        assert files_with_links == 0

    def test_direct_link_creates_shared_family(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe_a = make_rfe("RHAIRFE-1", links=[
            {"type": "Duplicate", "direction": "outward", "key": "RHAIRFE-2"}
        ])
        rfe_b = make_rfe("RHAIRFE-2", links=[
            {"type": "Duplicate", "direction": "inward", "key": "RHAIRFE-1"}
        ])
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(rfe_a))
        (rfes_dir / "RHAIRFE-2.json").write_text(json.dumps(rfe_b))

        key_to_family, num_families, _, _ = filter_candidates.build_link_families(
            rfes_dir, ["Duplicate"]
        )
        assert key_to_family["RHAIRFE-1"] == key_to_family["RHAIRFE-2"]
        assert num_families == 1

    def test_transitive_links_share_single_family(self, tmp_path):
        # A->B and B->C: A, B, C all belong to the same family even without A->C.
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe_a = make_rfe("RHAIRFE-1", links=[
            {"type": "Issue split", "direction": "outward", "key": "RHAIRFE-2"}
        ])
        rfe_b = make_rfe("RHAIRFE-2", links=[
            {"type": "Issue split", "direction": "outward", "key": "RHAIRFE-3"}
        ])
        rfe_c = make_rfe("RHAIRFE-3")
        for key, rfe in [("RHAIRFE-1", rfe_a), ("RHAIRFE-2", rfe_b), ("RHAIRFE-3", rfe_c)]:
            (rfes_dir / f"{key}.json").write_text(json.dumps(rfe))

        key_to_family, _, _, _ = filter_candidates.build_link_families(rfes_dir, ["Issue split"])
        assert key_to_family["RHAIRFE-1"] == key_to_family["RHAIRFE-2"]
        assert key_to_family["RHAIRFE-2"] == key_to_family["RHAIRFE-3"]

    def test_unrelated_link_type_not_counted(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe_a = make_rfe("RHAIRFE-1", links=[
            {"type": "Relates", "direction": "outward", "key": "RHAIRFE-2"}
        ])
        rfe_b = make_rfe("RHAIRFE-2")
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(rfe_a))
        (rfes_dir / "RHAIRFE-2.json").write_text(json.dumps(rfe_b))

        key_to_family, num_families, _, _ = filter_candidates.build_link_families(
            rfes_dir, ["Issue split", "Duplicate"]
        )
        assert "RHAIRFE-1" not in key_to_family
        assert num_families == 0

    def test_files_with_links_counts_only_matching_types(self, tmp_path):
        # RFE-1 has only a "Relates" link (not in filter set).
        # files_with_links should be 0, not 1, so the "may be cached" warning fires correctly.
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe_a = make_rfe("RHAIRFE-1", links=[
            {"type": "Relates", "direction": "outward", "key": "RHAIRFE-2"}
        ])
        rfe_b = make_rfe("RHAIRFE-2")
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(rfe_a))
        (rfes_dir / "RHAIRFE-2.json").write_text(json.dumps(rfe_b))

        _, _, _, files_with_links = filter_candidates.build_link_families(
            rfes_dir, ["Issue split", "Duplicate"]
        )
        assert files_with_links == 0

    def test_skips_meta_json(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        (rfes_dir / "_meta.json").write_text('{"jql": "...", "total": 0}')
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(make_rfe("RHAIRFE-1")))
        key_to_family, _, _, _ = filter_candidates.build_link_families(rfes_dir, ["Duplicate"])
        assert isinstance(key_to_family, dict)

    def test_two_independent_families(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe1 = make_rfe("RHAIRFE-1", links=[
            {"type": "Duplicate", "direction": "outward", "key": "RHAIRFE-2"}
        ])
        rfe2 = make_rfe("RHAIRFE-2")
        rfe3 = make_rfe("RHAIRFE-3", links=[
            {"type": "Duplicate", "direction": "outward", "key": "RHAIRFE-4"}
        ])
        rfe4 = make_rfe("RHAIRFE-4")
        for key, rfe in [("RHAIRFE-1", rfe1), ("RHAIRFE-2", rfe2),
                         ("RHAIRFE-3", rfe3), ("RHAIRFE-4", rfe4)]:
            (rfes_dir / f"{key}.json").write_text(json.dumps(rfe))

        key_to_family, num_families, _, _ = filter_candidates.build_link_families(
            rfes_dir, ["Duplicate"]
        )
        assert num_families == 2
        assert key_to_family["RHAIRFE-1"] != key_to_family["RHAIRFE-3"]

    def test_link_type_counts_tracked(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        rfe_a = make_rfe("RHAIRFE-1", links=[
            {"type": "Duplicate", "direction": "outward", "key": "RHAIRFE-2"},
            {"type": "Issue split", "direction": "outward", "key": "RHAIRFE-3"},
        ])
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(rfe_a))
        (rfes_dir / "RHAIRFE-2.json").write_text(json.dumps(make_rfe("RHAIRFE-2")))
        (rfes_dir / "RHAIRFE-3.json").write_text(json.dumps(make_rfe("RHAIRFE-3")))

        _, _, type_counts, _ = filter_candidates.build_link_families(
            rfes_dir, ["Duplicate", "Issue split"]
        )
        assert type_counts["Duplicate"] >= 1
        assert type_counts["Issue split"] >= 1


class TestFilterCandidates:
    def test_removes_pair_in_same_family(self):
        family = frozenset(["RHAIRFE-1", "RHAIRFE-2"])
        key_to_family = {"RHAIRFE-1": family, "RHAIRFE-2": family}
        candidates = [make_candidate("RHAIRFE-1", "RHAIRFE-2")]
        filtered, removed = filter_candidates.filter_candidates(candidates, key_to_family)
        assert len(filtered) == 0
        assert removed == 1

    def test_keeps_pair_in_different_families(self):
        key_to_family = {
            "RHAIRFE-1": frozenset(["RHAIRFE-1"]),
            "RHAIRFE-2": frozenset(["RHAIRFE-2"]),
        }
        candidates = [make_candidate("RHAIRFE-1", "RHAIRFE-2")]
        filtered, removed = filter_candidates.filter_candidates(candidates, key_to_family)
        assert len(filtered) == 1
        assert removed == 0

    def test_keeps_pair_where_neither_is_linked(self):
        candidates = [make_candidate("RHAIRFE-1", "RHAIRFE-2")]
        filtered, removed = filter_candidates.filter_candidates(candidates, {})
        assert len(filtered) == 1
        assert removed == 0

    def test_keeps_pair_where_only_one_has_family(self):
        # rfe_a is in a family with rfe_c, but rfe_b is not linked at all.
        # Since rfe_b has no family entry, it cannot be in rfe_a's family.
        family = frozenset(["RHAIRFE-1", "RHAIRFE-3"])
        key_to_family = {"RHAIRFE-1": family, "RHAIRFE-3": family}
        candidates = [make_candidate("RHAIRFE-1", "RHAIRFE-2")]
        filtered, removed = filter_candidates.filter_candidates(candidates, key_to_family)
        assert len(filtered) == 1
        assert removed == 0

    def test_empty_candidates_returns_empty(self):
        filtered, removed = filter_candidates.filter_candidates([], {})
        assert filtered == []
        assert removed == 0

    def test_mixed_candidates_filtered_correctly(self):
        family = frozenset(["RHAIRFE-1", "RHAIRFE-2"])
        key_to_family = {"RHAIRFE-1": family, "RHAIRFE-2": family}
        candidates = [
            make_candidate("RHAIRFE-1", "RHAIRFE-2", 0.95),  # same family - removed
            make_candidate("RHAIRFE-1", "RHAIRFE-3", 0.85),  # different family - kept
        ]
        filtered, removed = filter_candidates.filter_candidates(candidates, key_to_family)
        assert len(filtered) == 1
        assert removed == 1
        assert filtered[0]["rfe_b"] == "RHAIRFE-3"

    def test_sibling_pair_removed_transitively(self):
        # A and C are siblings (both split from B), so (A,C) should be filtered.
        family = frozenset(["RHAIRFE-A", "RHAIRFE-B", "RHAIRFE-C"])
        key_to_family = {
            "RHAIRFE-A": family,
            "RHAIRFE-B": family,
            "RHAIRFE-C": family,
        }
        candidates = [make_candidate("RHAIRFE-A", "RHAIRFE-C")]
        filtered, removed = filter_candidates.filter_candidates(candidates, key_to_family)
        assert removed == 1
        assert filtered == []
