import sys
import pytest
from pathlib import Path

import group_metadata


def make_group_file(groups_dir, num, rfe_keys):
    lines = []
    for key in rfe_keys:
        lines.append(f"### {key}: Summary text for {key}")
        lines.append("- **Priority:** Major")
        lines.append("- **Components:** Auth")
        lines.append("")
    (groups_dir / f"group_{num:02d}.md").write_text("\n".join(lines))


class TestGroupMetadataMain:
    def test_prints_tsv_for_each_group(self, tmp_path, monkeypatch, capsys):
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()
        make_group_file(groups_dir, 1, ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-3"])
        make_group_file(groups_dir, 2, ["RHAIRFE-4", "RHAIRFE-5"])

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        group_metadata.main()

        lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
        assert len(lines) == 2
        # First group: number=1, member_count=3
        fields = lines[0].split("\t")
        assert fields[0] == "1"
        assert fields[1] == "3"

    def test_exits_when_no_group_files(self, tmp_path, monkeypatch, capsys):
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        with pytest.raises(SystemExit) as exc_info:
            group_metadata.main()

        assert exc_info.value.code == 1
        assert "No group files found" in capsys.readouterr().err

    def test_single_member_group(self, tmp_path, monkeypatch, capsys):
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()
        make_group_file(groups_dir, 1, ["RHAIRFE-99"])

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        group_metadata.main()

        output = capsys.readouterr().out.strip()
        assert output == "1\t1"

    def test_group_number_extracted_from_filename(self, tmp_path, monkeypatch, capsys):
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()
        make_group_file(groups_dir, 7, ["RHAIRFE-10", "RHAIRFE-20"])

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        group_metadata.main()

        output = capsys.readouterr().out.strip()
        assert output.startswith("7\t")

    def test_only_uppercase_key_headers_counted(self, tmp_path, monkeypatch, capsys):
        # Headers not matching '### [A-Z]+-\d+:' should not be counted.
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()
        content = (
            "### Not-Valid:\n"             # no digits, won't match
            "### rhairfe-1234: lowercase\n"  # lowercase, won't match
            "### RHAIRFE-1234: Valid\n"    # matches
            "### ABC-999: Also valid\n"    # matches
        )
        (groups_dir / "group_01.md").write_text(content)

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        group_metadata.main()

        output = capsys.readouterr().out.strip()
        assert output == "1\t2"

    def test_multiple_groups_reported_in_order(self, tmp_path, monkeypatch, capsys):
        groups_dir = tmp_path / "groups"
        groups_dir.mkdir()
        make_group_file(groups_dir, 1, ["RHAIRFE-1"])
        make_group_file(groups_dir, 2, ["RHAIRFE-2", "RHAIRFE-3"])
        make_group_file(groups_dir, 3, ["RHAIRFE-4", "RHAIRFE-5", "RHAIRFE-6"])

        monkeypatch.setattr(sys, "argv", ["group_metadata.py", "--groups-dir", str(groups_dir)])
        group_metadata.main()

        lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
        assert len(lines) == 3
        counts = [int(l.split("\t")[1]) for l in lines]
        assert counts == [1, 2, 3]
