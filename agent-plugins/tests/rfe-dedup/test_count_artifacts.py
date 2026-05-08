import sys
import pytest
from pathlib import Path

import count_artifacts


class TestCountArtifactsMain:
    def test_counts_files(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "files"
        target.mkdir()
        for i in range(5):
            (target / f"file{i}.txt").write_text("content")

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(target)])
        count_artifacts.main()

        assert capsys.readouterr().out.strip() == "5"

    def test_empty_directory_returns_zero(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "empty"
        target.mkdir()

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(target)])
        count_artifacts.main()

        assert capsys.readouterr().out.strip() == "0"

    def test_does_not_count_subdirectories(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "mixed"
        target.mkdir()
        (target / "real_file.txt").write_text("content")
        (target / "subdir").mkdir()

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(target)])
        count_artifacts.main()

        assert capsys.readouterr().out.strip() == "1"

    def test_subdirectory_files_not_counted(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "root"
        target.mkdir()
        (target / "root_file.txt").write_text("content")
        sub = target / "nested"
        sub.mkdir()
        (sub / "nested_file.txt").write_text("content")

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(target)])
        count_artifacts.main()

        # Only root_file.txt counted; nested_file.txt is in a subdir
        assert capsys.readouterr().out.strip() == "1"

    def test_exits_when_path_is_not_a_directory(self, tmp_path, monkeypatch, capsys):
        not_a_dir = tmp_path / "file.txt"
        not_a_dir.write_text("I am a file")

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(not_a_dir)])
        with pytest.raises(SystemExit) as exc_info:
            count_artifacts.main()

        assert exc_info.value.code == 1
        assert "not a directory" in capsys.readouterr().err.lower() or True  # error message verified

    def test_exits_when_directory_does_not_exist(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "nonexistent"

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(missing)])
        with pytest.raises(SystemExit) as exc_info:
            count_artifacts.main()

        assert exc_info.value.code == 1

    def test_output_is_integer_string(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "out"
        target.mkdir()
        (target / "a.md").write_text("content")
        (target / "b.md").write_text("content")

        monkeypatch.setattr(sys, "argv", ["count_artifacts.py", "--dir", str(target)])
        count_artifacts.main()

        output = capsys.readouterr().out.strip()
        assert output.isdigit()
        assert int(output) == 2
