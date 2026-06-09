import json
import sys
import pytest
from pathlib import Path

import merge_matches


def make_match_result(rfe_a, rfe_b, degree):
    return {
        "rfe_a": rfe_a,
        "rfe_b": rfe_b,
        "match_degree": degree,
        "match_degree_label": "Partial",
        "overlap_type": "business_need",
        "overlap_description": "Some overlap",
        "unique_to_a": "",
        "unique_to_b": "",
        "merge_feasible": True,
        "merge_concern": None,
        "intentional_decomposition": False,
        "analysis_notes": "",
    }


def write_match(match_dir, num, data):
    (match_dir / f"match_{num:03d}.json").write_text(json.dumps(data))


class TestMergeMatchesMain:
    def test_merges_all_confirmed_matches(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        write_match(match_dir, 1, make_match_result("RHAIRFE-1", "RHAIRFE-2", 3))
        write_match(match_dir, 2, make_match_result("RHAIRFE-3", "RHAIRFE-4", 4))
        output = tmp_path / "confirmed_matches.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        data = json.loads(output.read_text())
        assert len(data) == 2

    def test_filters_degree_one_matches(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        write_match(match_dir, 1, make_match_result("RHAIRFE-1", "RHAIRFE-2", 1))  # no overlap
        write_match(match_dir, 2, make_match_result("RHAIRFE-3", "RHAIRFE-4", 2))  # kept

        output = tmp_path / "confirmed.json"
        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        data = json.loads(output.read_text())
        assert len(data) == 1
        assert data[0]["rfe_a"] == "RHAIRFE-3"

    def test_all_degrees_two_through_five_kept(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        for i, degree in enumerate([2, 3, 4, 5], start=1):
            write_match(match_dir, i, make_match_result(f"A-{i}", f"B-{i}", degree))

        output = tmp_path / "confirmed.json"
        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        data = json.loads(output.read_text())
        assert len(data) == 4

    def test_empty_match_dir_exits_nonzero(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        output = tmp_path / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        with pytest.raises(SystemExit) as exc_info:
            merge_matches.main()
        assert exc_info.value.code == 1

    def test_string_match_degree_filtered_not_crash(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        bad = {"rfe_a": "X-1", "rfe_b": "X-2", "match_degree": "high"}
        (match_dir / "match_001.json").write_text(json.dumps(bad))
        write_match(match_dir, 2, make_match_result("RHAIRFE-3", "RHAIRFE-4", 3))
        output = tmp_path / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        data = json.loads(output.read_text())
        assert len(data) == 1
        assert data[0]["rfe_a"] == "RHAIRFE-3"

    def test_skips_malformed_file_missing_match_degree(self, tmp_path, monkeypatch, capsys):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        # Missing match_degree key
        (match_dir / "match_001.json").write_text(json.dumps({"rfe_a": "X-1", "rfe_b": "X-2"}))
        write_match(match_dir, 2, make_match_result("RHAIRFE-3", "RHAIRFE-4", 3))
        output = tmp_path / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        captured = capsys.readouterr()
        assert "skipping malformed" in captured.err
        data = json.loads(output.read_text())
        assert len(data) == 1

    def test_skips_invalid_json_file(self, tmp_path, monkeypatch, capsys):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        (match_dir / "match_001.json").write_text("not valid json {{{{")
        output = tmp_path / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        captured = capsys.readouterr()
        assert "skipping unreadable" in captured.err

    def test_warns_on_gap_in_sequence(self, tmp_path, monkeypatch, capsys):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        write_match(match_dir, 1, make_match_result("RHAIRFE-1", "RHAIRFE-2", 3))
        # match_002 missing
        write_match(match_dir, 3, make_match_result("RHAIRFE-3", "RHAIRFE-4", 3))
        output = tmp_path / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        captured = capsys.readouterr()
        assert "missing" in captured.err.lower()
        # Both valid matches still written
        data = json.loads(output.read_text())
        assert len(data) == 2

    def test_output_parent_directory_created_if_missing(self, tmp_path, monkeypatch):
        match_dir = tmp_path / "match_results"
        match_dir.mkdir()
        write_match(match_dir, 1, make_match_result("RHAIRFE-1", "RHAIRFE-2", 3))
        output = tmp_path / "nested" / "deeply" / "confirmed.json"

        monkeypatch.setattr(sys, "argv", [
            "merge_matches.py",
            "--match-dir", str(match_dir),
            "--output", str(output),
        ])
        merge_matches.main()

        assert output.exists()
