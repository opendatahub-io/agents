import json
import sys
import pytest
from pathlib import Path

import find_missing_pairs


def make_match(rfe_a, rfe_b, degree=3):
    return {
        "rfe_a": rfe_a,
        "rfe_b": rfe_b,
        "match_degree": degree,
        "match_degree_label": "Partial",
    }


def make_rfe(key, summary="Summary", description="Description", comments=None):
    return {
        "key": key,
        "summary": summary,
        "description": description,
        "comments": comments or [],
    }


class TestFindConnectedComponents:
    def test_single_pair_forms_one_group(self):
        matches = [make_match("RHAIRFE-1", "RHAIRFE-2")]
        groups = find_missing_pairs.find_connected_components(matches)
        assert len(groups) == 1
        assert sorted(groups[0]) == ["RHAIRFE-1", "RHAIRFE-2"]

    def test_chain_forms_single_group(self):
        matches = [make_match("A", "B"), make_match("B", "C")]
        groups = find_missing_pairs.find_connected_components(matches)
        assert len(groups) == 1
        assert sorted(groups[0]) == ["A", "B", "C"]

    def test_two_disjoint_pairs_form_two_groups(self):
        matches = [make_match("A", "B"), make_match("C", "D")]
        groups = find_missing_pairs.find_connected_components(matches)
        assert len(groups) == 2

    def test_groups_sorted_by_size_descending(self):
        matches = [
            make_match("A", "B"),
            make_match("B", "C"),
            make_match("D", "E"),
        ]
        groups = find_missing_pairs.find_connected_components(matches)
        sizes = [len(g) for g in groups]
        assert sizes[0] >= sizes[-1]

    def test_returns_lists_not_dicts(self):
        # find_missing_pairs version returns lists, not group dicts like form_groups
        matches = [make_match("A", "B")]
        groups = find_missing_pairs.find_connected_components(matches)
        assert isinstance(groups[0], list)

    def test_members_sorted_within_group(self):
        matches = [make_match("RHAIRFE-5", "RHAIRFE-1")]
        groups = find_missing_pairs.find_connected_components(matches)
        assert groups[0] == sorted(groups[0])

    def test_empty_matches_returns_empty(self):
        assert find_missing_pairs.find_connected_components([]) == []


class TestScanEvaluatedPairs:
    def test_returns_empty_set_for_nonexistent_dir(self, tmp_path):
        result = find_missing_pairs.scan_evaluated_pairs(tmp_path / "nonexistent")
        assert result == set()

    def test_finds_evaluated_pair(self, tmp_path):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        (match_dir / "match_001.json").write_text(json.dumps({
            "rfe_a": "RHAIRFE-1",
            "rfe_b": "RHAIRFE-2",
            "match_degree": 1,
        }))
        result = find_missing_pairs.scan_evaluated_pairs(match_dir)
        assert ("RHAIRFE-1", "RHAIRFE-2") in result

    def test_pair_key_always_sorted(self, tmp_path):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        (match_dir / "match_001.json").write_text(json.dumps({
            "rfe_a": "RHAIRFE-9",
            "rfe_b": "RHAIRFE-1",
            "match_degree": 2,
        }))
        result = find_missing_pairs.scan_evaluated_pairs(match_dir)
        assert ("RHAIRFE-1", "RHAIRFE-9") in result
        assert ("RHAIRFE-9", "RHAIRFE-1") not in result

    def test_skips_invalid_json(self, tmp_path):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        (match_dir / "match_001.json").write_text("invalid {{{{")
        result = find_missing_pairs.scan_evaluated_pairs(match_dir)
        assert result == set()

    def test_skips_file_missing_rfe_keys(self, tmp_path):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        (match_dir / "match_001.json").write_text(json.dumps({"match_degree": 1}))
        result = find_missing_pairs.scan_evaluated_pairs(match_dir)
        assert result == set()

    def test_collects_multiple_evaluated_pairs(self, tmp_path):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        for i in range(3):
            (match_dir / f"match_{i:03d}.json").write_text(json.dumps({
                "rfe_a": f"RHAIRFE-{i*2+1}",
                "rfe_b": f"RHAIRFE-{i*2+2}",
                "match_degree": 1,
            }))
        result = find_missing_pairs.scan_evaluated_pairs(match_dir)
        assert len(result) == 3


class TestFormatPairMarkdownGapFill:
    def test_header_contains_gap_fill_label(self):
        rfe_a = make_rfe("RHAIRFE-1")
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 5)
        assert "gap fill" in result

    def test_header_shows_index_and_total(self):
        rfe_a = make_rfe("RHAIRFE-1")
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 3, 10)
        assert "Pair 3/10" in result

    def test_contains_both_rfe_keys(self):
        rfe_a = make_rfe("RHAIRFE-1234")
        rfe_b = make_rfe("RHAIRFE-5678")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 1)
        assert "RHAIRFE-1234" in result
        assert "RHAIRFE-5678" in result

    def test_includes_description(self):
        rfe_a = make_rfe("RHAIRFE-1", description="Specific feature request")
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 1)
        assert "Specific feature request" in result

    def test_long_description_truncated(self):
        rfe_a = make_rfe("RHAIRFE-1", description="x" * 3000)
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 1)
        assert "...[truncated]" in result

    def test_comments_included_as_blockquotes(self):
        rfe_a = make_rfe("RHAIRFE-1", comments=[{"body": "Important note"}])
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 1)
        assert "> Comment: Important note" in result

    def test_comments_shown_newest_first(self):
        comments = [
            {"body": "Oldest comment"},
            {"body": "Middle comment"},
            {"body": "Newest comment"},
        ]
        rfe_a = make_rfe("RHAIRFE-1", comments=comments)
        rfe_b = make_rfe("RHAIRFE-2")
        result = find_missing_pairs.format_pair_markdown(rfe_a, rfe_b, 1, 1)
        newest_pos = result.find("Newest comment")
        oldest_pos = result.find("Oldest comment")
        assert newest_pos != -1
        assert oldest_pos != -1
        assert newest_pos < oldest_pos


class TestFindMissingPairsMainIntegration:
    def _write_confirmed(self, path, matches):
        path.write_text(json.dumps(matches))

    def test_no_gaps_prints_message(self, tmp_path, monkeypatch, capsys):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()

        # Group: A-B-C (all 3 pairs evaluated)
        confirmed = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 4),
            make_match("RHAIRFE-1", "RHAIRFE-3", 4),
            make_match("RHAIRFE-2", "RHAIRFE-3", 4),
        ]
        for rfe in ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"]:
            (rfes_dir / f"{rfe}.json").write_text(json.dumps(make_rfe(rfe)))
        confirmed_path = tmp_path / "confirmed_matches.json"
        self._write_confirmed(confirmed_path, confirmed)

        monkeypatch.setattr(sys, "argv", [
            "find_missing_pairs.py",
            "--confirmed-matches", str(confirmed_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(tmp_path),
            "--match-dir", str(match_dir),
        ])
        find_missing_pairs.main()

        captured = capsys.readouterr()
        assert "all pairs already evaluated" in captured.err
        assert not (tmp_path / "gap_pairs").exists()

    def test_identifies_missing_intra_group_pair(self, tmp_path, monkeypatch, capsys):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()

        # Group formed by A-B and A-C, but B-C was never evaluated
        confirmed = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-1", "RHAIRFE-3", 3),
        ]
        for rfe in ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"]:
            (rfes_dir / f"{rfe}.json").write_text(json.dumps(make_rfe(rfe)))
        confirmed_path = tmp_path / "confirmed_matches.json"
        self._write_confirmed(confirmed_path, confirmed)

        monkeypatch.setattr(sys, "argv", [
            "find_missing_pairs.py",
            "--confirmed-matches", str(confirmed_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(tmp_path),
            "--match-dir", str(match_dir),
        ])
        find_missing_pairs.main()

        gap_files = list((tmp_path / "gap_pairs").glob("pair_*.md"))
        assert len(gap_files) == 1

    def test_degree_one_already_evaluated_pair_not_repeated(self, tmp_path, monkeypatch, capsys):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()

        # Group: A-B and A-C; B-C was evaluated at degree 1 (no overlap) but not confirmed
        confirmed = [
            make_match("RHAIRFE-1", "RHAIRFE-2", 3),
            make_match("RHAIRFE-1", "RHAIRFE-3", 3),
        ]
        # B-C was evaluated at degree 1 (not in confirmed, but IS in match_results)
        (match_dir / "match_001.json").write_text(json.dumps({
            "rfe_a": "RHAIRFE-2",
            "rfe_b": "RHAIRFE-3",
            "match_degree": 1,
        }))
        for rfe in ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"]:
            (rfes_dir / f"{rfe}.json").write_text(json.dumps(make_rfe(rfe)))
        confirmed_path = tmp_path / "confirmed_matches.json"
        self._write_confirmed(confirmed_path, confirmed)

        monkeypatch.setattr(sys, "argv", [
            "find_missing_pairs.py",
            "--confirmed-matches", str(confirmed_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(tmp_path),
            "--match-dir", str(match_dir),
        ])
        find_missing_pairs.main()

        # B-C should NOT appear in gap_pairs since it was already evaluated at degree 1
        captured = capsys.readouterr()
        assert "all pairs already evaluated" in captured.err
