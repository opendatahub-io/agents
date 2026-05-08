import json
import pytest

import find_candidates


class TestBuildText:
    def test_summary_and_description_included(self):
        issue = {"key": "X-1", "summary": "A summary", "description": "A description"}
        result = find_candidates.build_text(issue)
        assert "A summary" in result
        assert "A description" in result

    def test_empty_description_not_added(self):
        issue = {"key": "X-1", "summary": "Just a title", "description": ""}
        result = find_candidates.build_text(issue)
        assert "Just a title" in result
        assert result.endswith("Just a title")

    def test_no_comments_uses_only_summary_and_description(self):
        issue = {"key": "X-1", "summary": "S", "description": "D", "comments": []}
        assert find_candidates.build_text(issue) == "S\n\nD"

    def test_missing_comments_key_handled(self):
        issue = {"key": "X-1", "summary": "S", "description": "D"}
        result = find_candidates.build_text(issue)
        assert result == "S\n\nD"

    def test_comments_appended_newest_first(self):
        issue = {
            "key": "X-1",
            "summary": "S",
            "description": "D",
            "comments": [
                {"body": "Oldest comment"},
                {"body": "Middle comment"},
                {"body": "Newest comment"},
            ],
        }
        result = find_candidates.build_text(issue)
        newest_pos = result.find("Newest comment")
        oldest_pos = result.find("Oldest comment")
        assert newest_pos != -1
        assert oldest_pos != -1
        assert newest_pos < oldest_pos

    def test_empty_comment_body_skipped(self):
        issue = {
            "key": "X-1",
            "summary": "S",
            "description": "D",
            "comments": [{"body": ""}, {"body": "Real comment"}],
        }
        result = find_candidates.build_text(issue)
        assert "Real comment" in result

    def test_long_core_text_limits_comment_inclusion(self):
        # When summary+description exceeds MAX_TEXT_CHARS, comments are not added.
        long_description = "x" * find_candidates.MAX_TEXT_CHARS
        issue = {
            "key": "X-1",
            "summary": "S",
            "description": long_description,
            "comments": [{"body": "SHOULD_NOT_APPEAR"}],
        }
        result = find_candidates.build_text(issue)
        assert "SHOULD_NOT_APPEAR" not in result

    def test_comments_truncated_to_remaining_space(self):
        # Core text uses most of MAX_TEXT_CHARS; only a small slice of comments fits.
        core_size = find_candidates.MAX_TEXT_CHARS - 200
        issue = {
            "key": "X-1",
            "summary": "S",
            "description": "D" * core_size,
            "comments": [{"body": "C" * 5000}],
        }
        result = find_candidates.build_text(issue)
        assert len(result) <= find_candidates.MAX_TEXT_CHARS + 10  # +10 for newlines

    def test_missing_summary_handled(self):
        issue = {"key": "X-1", "description": "Only a description"}
        result = find_candidates.build_text(issue)
        assert "Only a description" in result


class TestLoadRfes:
    def test_yields_key_text_pairs(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        issue = {"key": "RHAIRFE-1", "summary": "Test", "description": "Desc", "comments": []}
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(issue))
        results = list(find_candidates.load_rfes(rfes_dir))
        assert len(results) == 1
        key, text = results[0]
        assert key == "RHAIRFE-1"
        assert "Test" in text

    def test_skips_meta_json(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        (rfes_dir / "_meta.json").write_text('{"jql": "...", "fetched_at": 0, "total": 1}')
        issue = {"key": "RHAIRFE-1", "summary": "Test", "description": "", "comments": []}
        (rfes_dir / "RHAIRFE-1.json").write_text(json.dumps(issue))
        results = list(find_candidates.load_rfes(rfes_dir))
        assert len(results) == 1
        assert results[0][0] == "RHAIRFE-1"

    def test_empty_dir_yields_nothing(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        results = list(find_candidates.load_rfes(rfes_dir))
        assert results == []

    def test_only_meta_json_yields_nothing(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        (rfes_dir / "_meta.json").write_text('{"jql": "test"}')
        results = list(find_candidates.load_rfes(rfes_dir))
        assert results == []

    def test_files_yielded_in_sorted_order(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        for key in ["RHAIRFE-30", "RHAIRFE-2", "RHAIRFE-15"]:
            issue = {"key": key, "summary": key, "description": "", "comments": []}
            (rfes_dir / f"{key}.json").write_text(json.dumps(issue))
        keys = [k for k, _ in find_candidates.load_rfes(rfes_dir)]
        assert keys == sorted(keys)

    def test_multiple_rfes_all_yielded(self, tmp_path):
        rfes_dir = tmp_path / "rfes"
        rfes_dir.mkdir()
        for i in range(5):
            issue = {"key": f"RHAIRFE-{i}", "summary": f"Issue {i}", "description": "", "comments": []}
            (rfes_dir / f"RHAIRFE-{i}.json").write_text(json.dumps(issue))
        results = list(find_candidates.load_rfes(rfes_dir))
        assert len(results) == 5
