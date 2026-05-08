import sys
import pytest
from pathlib import Path

import create_run_dir


class TestNormalizeName:
    def test_plain_words_hyphenated(self):
        assert create_run_dir.normalize_name("new rhairfe rfes") == "dedup-new-rhairfe-rfes"

    def test_already_lowercase_unchanged(self):
        assert create_run_dir.normalize_name("agentdev component") == "dedup-agentdev-component"

    def test_uppercased_input_lowercased(self):
        assert create_run_dir.normalize_name("New RHAIRFE RFEs") == "dedup-new-rhairfe-rfes"

    def test_dots_become_hyphens(self):
        assert create_run_dir.normalize_name("3.5 candidate backlog") == "dedup-3-5-candidate-backlog"

    def test_multiple_spaces_collapse_to_one_hyphen(self):
        assert create_run_dir.normalize_name("a  b   c") == "dedup-a-b-c"

    def test_special_characters_become_hyphens(self):
        result = create_run_dir.normalize_name("status: new & open")
        assert result == "dedup-status-new-open"

    def test_leading_and_trailing_hyphens_stripped(self):
        result = create_run_dir.normalize_name("  spaced input  ")
        assert not result.startswith("dedup--")
        assert not result.endswith("-")

    def test_mixed_separators_collapse(self):
        result = create_run_dir.normalize_name("foo--bar__baz")
        assert result == "dedup-foo-bar-baz"

    def test_result_always_starts_with_dedup(self):
        assert create_run_dir.normalize_name("anything").startswith("dedup-")

    def test_numeric_characters_preserved(self):
        assert create_run_dir.normalize_name("q3 2024 rfes") == "dedup-q3-2024-rfes"

    def test_single_word(self):
        assert create_run_dir.normalize_name("backlog") == "dedup-backlog"

    def test_hyphenated_input_preserved(self):
        assert create_run_dir.normalize_name("3.5-candidate") == "dedup-3-5-candidate"


class TestCreateRunDirMain:
    def test_creates_directory_and_prints_path(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "new rhairfe rfes",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        created = Path(output)
        assert created.exists()
        assert created.is_dir()

    def test_printed_path_is_within_base_dir(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "agentdev component",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        assert Path(output).parent == tmp_path

    def test_name_normalized_in_directory_name(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "New RHAIRFE RFEs",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        assert Path(output).name == "dedup-new-rhairfe-rfes"

    def test_collision_appends_suffix_1(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "dedup-new-rhairfe-rfes").mkdir()

        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "new rhairfe rfes",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        created = Path(output)
        assert created.exists()
        assert created.name == "dedup-new-rhairfe-rfes-1"

    def test_multiple_collisions_increment_suffix(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "dedup-new-rhairfe-rfes").mkdir()
        (tmp_path / "dedup-new-rhairfe-rfes-1").mkdir()

        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "new rhairfe rfes",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        assert Path(output).name == "dedup-new-rhairfe-rfes-2"

    def test_created_directory_is_empty(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "backlog analysis",
            "--base-dir", str(tmp_path),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        assert list(Path(output).iterdir()) == []

    def test_base_dir_created_if_missing(self, tmp_path, monkeypatch, capsys):
        nested_base = tmp_path / "nested" / "base"
        monkeypatch.setattr(sys, "argv", [
            "create_run_dir.py",
            "--name", "test run",
            "--base-dir", str(nested_base),
        ])
        create_run_dir.main()

        output = capsys.readouterr().out.strip()
        assert Path(output).exists()
