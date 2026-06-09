import json
import sys
import pytest
from pathlib import Path

import assemble_report

BASE_ARGS = [
    "--jql", "project = RHAIRFE AND status = New",
    "--date", "2024-01-15",
    "--rfe-count", "100",
    "--group-count", "5",
]


class TestAssembleReportMain:
    def test_assembles_all_sections_into_output(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("## Group 1\nContent A\n")
        (reports_dir / "report_02.md").write_text("## Group 2\nContent B\n")
        output = tmp_path / "dedup_report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        content = output.read_text()
        assert "Content A" in content
        assert "Content B" in content

    def test_header_written_before_sections(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("section content")
        output = tmp_path / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
            "--jql", "project = RHAIRFE",
            "--date", "2024-03-01",
            "--rfe-count", "50",
            "--group-count", "3",
        ])
        assemble_report.main()

        content = output.read_text()
        header_pos = content.find("RFE Duplicate Analysis Report")
        section_pos = content.find("section content")
        assert header_pos != -1
        assert section_pos != -1
        assert header_pos < section_pos

    def test_header_contains_jql_and_date(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        output = tmp_path / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
            "--jql", "project = MYPROJECT",
            "--date", "2024-06-15",
            "--rfe-count", "200",
            "--group-count", "10",
        ])
        assemble_report.main()

        content = output.read_text()
        assert "project = MYPROJECT" in content
        assert "2024-06-15" in content
        assert "200" in content

    def test_exits_when_no_report_files(self, tmp_path, monkeypatch, capsys):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        output = tmp_path / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)

        with pytest.raises(SystemExit) as exc_info:
            assemble_report.main()

        assert exc_info.value.code == 1
        assert "no report" in capsys.readouterr().err.lower()

    def test_json_output_written_when_companions_present(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        (reports_dir / "report_01.json").write_text(json.dumps({
            "group_number": 1,
            "recommendation": "Merge",
        }))
        output = tmp_path / "dedup_report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        json_output = output.with_suffix(".json")
        assert json_output.exists()
        data = json.loads(json_output.read_text())
        assert "metadata" in data
        assert "group_reports" in data
        assert data["group_reports"][0]["recommendation"] == "Merge"

    def test_no_json_output_without_companions_or_summary(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        output = tmp_path / "dedup_report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        json_output = output.with_suffix(".json")
        assert not json_output.exists()

    def test_groups_summary_embedded_in_json(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        (reports_dir / "report_01.json").write_text(json.dumps({"group_number": 1}))

        summary = {"metadata": {"total_groups": 1}, "groups": [], "cross_group_refs": [], "ungrouped": []}
        gs_path = tmp_path / "groups_summary.json"
        gs_path.write_text(json.dumps(summary))
        output = tmp_path / "dedup_report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
            "--groups-summary", str(gs_path),
        ] + BASE_ARGS)
        assemble_report.main()

        json_output = output.with_suffix(".json")
        assert json_output.exists()
        data = json.loads(json_output.read_text())
        assert "groups_summary" in data
        assert data["groups_summary"]["metadata"]["total_groups"] == 1

    def test_json_written_with_only_groups_summary(self, tmp_path, monkeypatch):
        # groups_summary alone (no companion .json files) still produces JSON output.
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")

        summary = {"metadata": {"total_groups": 2}, "groups": []}
        gs_path = tmp_path / "groups_summary.json"
        gs_path.write_text(json.dumps(summary))
        output = tmp_path / "dedup_report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
            "--groups-summary", str(gs_path),
        ] + BASE_ARGS)
        assemble_report.main()

        json_output = output.with_suffix(".json")
        assert json_output.exists()

    def test_warns_on_missing_json_companions(self, tmp_path, monkeypatch, capsys):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("section 1")
        (reports_dir / "report_02.md").write_text("section 2")
        # Only report_01 has a companion JSON
        (reports_dir / "report_01.json").write_text(json.dumps({"group_number": 1}))
        output = tmp_path / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "missing" in captured.err.lower() or "unreadable" in captured.err.lower()

    def test_output_parent_created_if_missing(self, tmp_path, monkeypatch):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        output = tmp_path / "nested" / "output" / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        assert output.exists()

    def test_malformed_companion_json_skipped_with_warning(self, tmp_path, monkeypatch, capsys):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "report_01.md").write_text("content")
        (reports_dir / "report_01.json").write_text("not valid json {{{{")
        output = tmp_path / "report.md"

        monkeypatch.setattr(sys, "argv", [
            "assemble_report.py",
            "--reports-dir", str(reports_dir),
            "--output", str(output),
        ] + BASE_ARGS)
        assemble_report.main()

        captured = capsys.readouterr()
        assert "Warning" in captured.err
