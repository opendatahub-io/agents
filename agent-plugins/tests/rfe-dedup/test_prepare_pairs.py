import json
import sys
import pytest
from pathlib import Path

import prepare_pairs


def make_rfe(key, summary="Test summary", description="Test description", comments=None):
    return {
        "key": key,
        "summary": summary,
        "description": description,
        "comments": comments or [],
    }


class TestTruncate:
    def test_short_text_returned_unchanged(self):
        assert prepare_pairs.truncate("hello", 100) == "hello"

    def test_none_returns_empty_string(self):
        assert prepare_pairs.truncate(None, 100) == ""

    def test_empty_string_returned_as_is(self):
        assert prepare_pairs.truncate("", 100) == ""

    def test_text_exactly_at_limit_not_truncated(self):
        text = "x" * 100
        assert prepare_pairs.truncate(text, 100) == text

    def test_text_one_over_limit_gets_suffix(self):
        text = "x" * 101
        result = prepare_pairs.truncate(text, 100)
        assert result.endswith("...[truncated]")
        assert len(result) == 100 + len("...[truncated]")

    def test_truncated_prefix_matches_original(self):
        text = "abcdef" * 50
        result = prepare_pairs.truncate(text, 10)
        assert result.startswith("abcdefabcd")
        assert result.endswith("...[truncated]")

    def test_zero_limit_truncates_everything(self):
        result = prepare_pairs.truncate("hello", 0)
        assert result == "...[truncated]"


class TestFormatPairMarkdown:
    def test_header_shows_pair_number_and_total(self):
        rfe_a = make_rfe("RHAIRFE-1")
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.92, 3, 10)
        assert "Pair 3/10" in result

    def test_header_shows_similarity_score(self):
        rfe_a = make_rfe("RHAIRFE-1")
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.8234, 1, 1)
        assert "0.8234" in result

    def test_contains_both_rfe_keys(self):
        rfe_a = make_rfe("RHAIRFE-1234")
        rfe_b = make_rfe("RHAIRFE-5678")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.85, 1, 5)
        assert "RHAIRFE-1234" in result
        assert "RHAIRFE-5678" in result

    def test_contains_both_summaries(self):
        rfe_a = make_rfe("RHAIRFE-1", summary="SSO support needed")
        rfe_b = make_rfe("RHAIRFE-2", summary="SAML authentication")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.88, 1, 5)
        assert "SSO support needed" in result
        assert "SAML authentication" in result

    def test_long_description_truncated_with_suffix(self):
        long_desc = "x" * 3000
        rfe_a = make_rfe("RHAIRFE-1", description=long_desc)
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "...[truncated]" in result

    def test_short_description_not_truncated(self):
        rfe_a = make_rfe("RHAIRFE-1", description="Short")
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "Short" in result
        assert "...[truncated]" not in result

    def test_comments_appear_as_blockquotes(self):
        comments = [{"body": "This is a comment"}]
        rfe_a = make_rfe("RHAIRFE-1", comments=comments)
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "> Comment: This is a comment" in result

    def test_comments_shown_newest_first(self):
        comments = [
            {"body": "Oldest comment"},
            {"body": "Middle comment"},
            {"body": "Newest comment"},
        ]
        rfe_a = make_rfe("RHAIRFE-1", comments=comments)
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        newest_pos = result.find("Newest comment")
        oldest_pos = result.find("Oldest comment")
        assert newest_pos != -1
        assert oldest_pos != -1
        assert newest_pos < oldest_pos

    def test_at_most_three_comments_per_rfe(self):
        comments = [{"body": f"Comment {i}"} for i in range(6)]
        rfe_a = make_rfe("RHAIRFE-1", comments=comments)
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert result.count("> Comment:") <= 3

    def test_long_comment_body_truncated(self):
        comments = [{"body": "y" * 1000}]
        rfe_a = make_rfe("RHAIRFE-1", comments=comments)
        rfe_b = make_rfe("RHAIRFE-2")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        comment_lines = [l for l in result.splitlines() if l.startswith("> Comment:")]
        assert len(comment_lines) == 1
        assert "...[truncated]" in comment_lines[0]

    def test_rfe_without_summary_uses_fallback(self):
        rfe_a = {"key": "RHAIRFE-1", "description": ""}
        rfe_b = {"key": "RHAIRFE-2", "description": ""}
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "(no summary)" in result

    def test_empty_description_not_rendered(self):
        rfe_a = make_rfe("RHAIRFE-1", description="")
        rfe_b = make_rfe("RHAIRFE-2", description="Desc B")
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "Desc B" in result

    def test_no_comments_produces_no_blockquotes(self):
        rfe_a = make_rfe("RHAIRFE-1", comments=[])
        rfe_b = make_rfe("RHAIRFE-2", comments=[])
        result = prepare_pairs.format_pair_markdown(rfe_a, rfe_b, 0.9, 1, 1)
        assert "> Comment:" not in result


class TestPrepairPairsMainIntegration:
    def _write_candidates(self, path, candidates):
        data = {
            "model": "test",
            "threshold": 0.8,
            "k": 10,
            "total_rfes": 2,
            "total_candidates": len(candidates),
            "candidates": candidates,
        }
        path.write_text(json.dumps(data))

    def test_writes_pair_files(self, tmp_path, monkeypatch):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(make_rfe("RHAIRFE-1")))
        (rfes_dir / "RHAIRFE-2.json").write_text(json.dumps(make_rfe("RHAIRFE-2")))

        candidates_path = tmp_path / "candidates.json"
        self._write_candidates(
            candidates_path,
            [{"rfe_a": "RHAIRFE-1", "rfe_b": "RHAIRFE-2", "similarity_score": 0.9}],
        )
        output_dir = tmp_path / "output"

        monkeypatch.setattr(sys, "argv", [
            "prepare_pairs.py",
            "--candidates", str(candidates_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(output_dir),
        ])
        prepare_pairs.main()

        pair_files = list((output_dir / "pairs").glob("pair_*.md"))
        assert len(pair_files) == 1

    def test_max_pairs_limits_output(self, tmp_path, monkeypatch):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        for i in range(1, 6):
            (rfes_dir / f"RHAIRFE-{i}.json").write_text(json.dumps(make_rfe(f"RHAIRFE-{i}")))

        candidates = [
            {"rfe_a": f"RHAIRFE-{i}", "rfe_b": f"RHAIRFE-{i+1}", "similarity_score": 0.9}
            for i in range(1, 5)
        ]
        candidates_path = tmp_path / "candidates.json"
        self._write_candidates(candidates_path, candidates)
        output_dir = tmp_path / "output"

        monkeypatch.setattr(sys, "argv", [
            "prepare_pairs.py",
            "--candidates", str(candidates_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(output_dir),
            "--max-pairs", "2",
        ])
        prepare_pairs.main()

        pair_files = list((output_dir / "pairs").glob("pair_*.md"))
        assert len(pair_files) == 2

    def test_warns_and_skips_missing_rfe(self, tmp_path, monkeypatch, capsys):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(make_rfe("RHAIRFE-1")))
        # RHAIRFE-99 does not exist

        candidates_path = tmp_path / "candidates.json"
        self._write_candidates(
            candidates_path,
            [{"rfe_a": "RHAIRFE-1", "rfe_b": "RHAIRFE-99", "similarity_score": 0.9}],
        )
        output_dir = tmp_path / "output"

        monkeypatch.setattr(sys, "argv", [
            "prepare_pairs.py",
            "--candidates", str(candidates_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(output_dir),
        ])
        prepare_pairs.main()

        captured = capsys.readouterr()
        assert "Warning" in captured.err
        pair_files = list((output_dir / "pairs").glob("pair_*.md"))
        assert len(pair_files) == 0

    def test_creates_match_results_dir(self, tmp_path, monkeypatch):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        candidates_path = tmp_path / "candidates.json"
        self._write_candidates(candidates_path, [])
        output_dir = tmp_path / "output"

        monkeypatch.setattr(sys, "argv", [
            "prepare_pairs.py",
            "--candidates", str(candidates_path),
            "--rfes-dir", str(rfes_dir),
            "--output-dir", str(output_dir),
        ])
        prepare_pairs.main()

        assert (output_dir / "match_results").is_dir()
