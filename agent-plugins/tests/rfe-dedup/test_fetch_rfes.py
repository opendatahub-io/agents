import json
import time
import pytest

import fetch_rfes


class TestLuceneEscape:
    def test_plain_text_unchanged(self):
        assert fetch_rfes.lucene_escape("hello world") == "hello world"

    def test_empty_string(self):
        assert fetch_rfes.lucene_escape("") == ""

    def test_escapes_backslash_first(self):
        # Backslash must be escaped before other specials to avoid double-escaping.
        result = fetch_rfes.lucene_escape("a\\b")
        assert result == r"a\\b"

    def test_escapes_colon(self):
        assert fetch_rfes.lucene_escape("status:New") == r"status\:New"

    def test_escapes_plus(self):
        assert fetch_rfes.lucene_escape("a+b") == r"a\+b"

    def test_escapes_all_special_chars(self):
        for ch in r'+-&|!(){}[]^"~*?:\/':
            result = fetch_rfes.lucene_escape(ch)
            assert result == f"\\{ch}", f"Failed for char {ch!r}"

    def test_does_not_double_escape_backslash(self):
        result = fetch_rfes.lucene_escape("\\")
        assert result == "\\\\"
        assert result.count("\\") == 2


class TestJqlStringEscape:
    def test_plain_text_unchanged(self):
        assert fetch_rfes.jql_string_escape("hello world") == "hello world"

    def test_empty_string(self):
        assert fetch_rfes.jql_string_escape("") == ""

    def test_escapes_double_quote(self):
        assert fetch_rfes.jql_string_escape('say "hello"') == r'say \"hello\"'

    def test_escapes_backslash(self):
        assert fetch_rfes.jql_string_escape("a\\b") == r"a\\b"

    def test_backslash_before_quote_both_escaped(self):
        result = fetch_rfes.jql_string_escape('a\\"b')
        assert result == r'a\\\"b'

    def test_no_other_chars_escaped(self):
        text = "project = RHAIRFE AND status in (New, Open)"
        assert fetch_rfes.jql_string_escape(text) == text


class TestAdfToText:
    def test_string_passthrough(self):
        assert fetch_rfes.adf_to_text("plain text") == "plain text"

    def test_integer_returns_empty(self):
        assert fetch_rfes.adf_to_text(42) == ""

    def test_none_returns_empty(self):
        assert fetch_rfes.adf_to_text(None) == ""

    def test_list_returns_empty(self):
        assert fetch_rfes.adf_to_text([]) == ""

    def test_text_node(self):
        assert fetch_rfes.adf_to_text({"type": "text", "text": "hello"}) == "hello"

    def test_text_node_missing_text_key(self):
        assert fetch_rfes.adf_to_text({"type": "text"}) == ""

    def test_empty_content_list(self):
        assert fetch_rfes.adf_to_text({"type": "doc", "content": []}) == ""

    def test_paragraph_joins_text_children(self):
        node = {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "text", "text": " world"},
            ],
        }
        result = fetch_rfes.adf_to_text(node)
        assert "Hello" in result
        assert " world" in result

    def test_doc_with_two_paragraphs(self):
        node = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First paragraph"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second paragraph"}],
                },
            ],
        }
        result = fetch_rfes.adf_to_text(node)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_inline_type_joins_without_newline(self):
        # Types not in the newline set should join children with "".
        node = {
            "type": "strong",
            "content": [
                {"type": "text", "text": "bold"},
                {"type": "text", "text": "text"},
            ],
        }
        assert fetch_rfes.adf_to_text(node) == "boldtext"

    def test_heading_type_uses_newline_joiner(self):
        node = {
            "type": "heading",
            "content": [
                {"type": "text", "text": "Title"},
            ],
        }
        result = fetch_rfes.adf_to_text(node)
        assert "Title" in result

    def test_nested_structure(self):
        node = {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item one"}],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = fetch_rfes.adf_to_text(node)
        assert "Item one" in result


class TestParseIssue:
    def _make_issue(self, key="RHAIRFE-1", fields=None):
        return {"key": key, "fields": fields or {}}

    def test_extracts_key(self):
        result = fetch_rfes.parse_issue(self._make_issue("RHAIRFE-42"), False)
        assert result["key"] == "RHAIRFE-42"

    def test_basic_text_fields(self):
        issue = self._make_issue(fields={
            "summary": "My summary",
            "description": "My description",
            "status": {"name": "New"},
            "priority": {"name": "Major"},
            "components": [{"name": "Auth"}, {"name": "UI"}],
            "labels": ["label1", "label2"],
            "issuelinks": [],
        })
        result = fetch_rfes.parse_issue(issue, include_comments=False)
        assert result["summary"] == "My summary"
        assert result["description"] == "My description"
        assert result["status"] == "New"
        assert result["priority"] == "Major"
        assert result["components"] == ["Auth", "UI"]
        assert result["labels"] == ["label1", "label2"]
        assert result["links"] == []
        assert result["comments"] == []

    def test_missing_fields_default_to_empty(self):
        result = fetch_rfes.parse_issue(self._make_issue(), False)
        assert result["summary"] == ""
        assert result["description"] == ""
        assert result["status"] == ""
        assert result["priority"] == ""
        assert result["components"] == []
        assert result["labels"] == []

    def test_null_status_and_priority(self):
        issue = self._make_issue(fields={"status": None, "priority": None})
        result = fetch_rfes.parse_issue(issue, False)
        assert result["status"] == ""
        assert result["priority"] == ""

    def test_adf_description_converted(self):
        adf_desc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "ADF content here"}],
                }
            ],
        }
        issue = self._make_issue(fields={"description": adf_desc})
        result = fetch_rfes.parse_issue(issue, False)
        assert "ADF content here" in result["description"]

    def test_comments_included_when_flag_set(self):
        issue = self._make_issue(fields={
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "Alice"},
                        "created": "2024-01-01",
                        "body": "Test comment",
                    }
                ]
            }
        })
        result = fetch_rfes.parse_issue(issue, include_comments=True)
        assert len(result["comments"]) == 1
        assert result["comments"][0]["author"] == "Alice"
        assert result["comments"][0]["body"] == "Test comment"

    def test_comments_excluded_when_flag_false(self):
        issue = self._make_issue(fields={
            "comment": {
                "comments": [
                    {"author": {"displayName": "Alice"}, "created": "2024-01-01", "body": "Ignored"}
                ]
            }
        })
        result = fetch_rfes.parse_issue(issue, include_comments=False)
        assert result["comments"] == []

    def test_adf_comment_body_converted(self):
        adf_body = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "ADF comment text"}],
                }
            ],
        }
        issue = self._make_issue(fields={
            "comment": {
                "comments": [
                    {"author": {"displayName": "Bob"}, "created": "2024-01-01", "body": adf_body}
                ]
            }
        })
        result = fetch_rfes.parse_issue(issue, include_comments=True)
        assert "ADF comment text" in result["comments"][0]["body"]

    def test_inward_link_parsed(self):
        issue = self._make_issue(fields={
            "issuelinks": [
                {"type": {"name": "Duplicate"}, "inwardIssue": {"key": "RHAIRFE-99"}}
            ]
        })
        result = fetch_rfes.parse_issue(issue, False)
        assert len(result["links"]) == 1
        link = result["links"][0]
        assert link["type"] == "Duplicate"
        assert link["direction"] == "inward"
        assert link["key"] == "RHAIRFE-99"

    def test_outward_link_parsed(self):
        issue = self._make_issue(fields={
            "issuelinks": [
                {"type": {"name": "Issue split"}, "outwardIssue": {"key": "RHAIRFE-100"}}
            ]
        })
        result = fetch_rfes.parse_issue(issue, False)
        link = result["links"][0]
        assert link["direction"] == "outward"
        assert link["key"] == "RHAIRFE-100"

    def test_multiple_links(self):
        issue = self._make_issue(fields={
            "issuelinks": [
                {"type": {"name": "Duplicate"}, "inwardIssue": {"key": "RHAIRFE-10"}},
                {"type": {"name": "Issue split"}, "outwardIssue": {"key": "RHAIRFE-20"}},
            ]
        })
        result = fetch_rfes.parse_issue(issue, False)
        assert len(result["links"]) == 2


class TestLoadCache:
    def test_returns_none_if_file_missing(self, tmp_path):
        result = fetch_rfes.load_cache(tmp_path / "nonexistent.json", "project = RHAIRFE")
        assert result is None

    def test_returns_none_if_jql_differs(self, tmp_path):
        meta_path = tmp_path / "_meta.json"
        meta = {"jql": "project = OTHER", "fetched_at": time.time(), "total": 5}
        meta_path.write_text(json.dumps(meta))
        result = fetch_rfes.load_cache(meta_path, "project = RHAIRFE")
        assert result is None

    def test_returns_none_if_expired(self, tmp_path):
        meta_path = tmp_path / "_meta.json"
        old_time = time.time() - (5 * 3600)  # 5 hours old, beyond 4h TTL
        meta = {"jql": "project = RHAIRFE", "fetched_at": old_time, "total": 5}
        meta_path.write_text(json.dumps(meta))
        result = fetch_rfes.load_cache(meta_path, "project = RHAIRFE")
        assert result is None

    def test_returns_meta_if_fresh_and_matching(self, tmp_path):
        meta_path = tmp_path / "_meta.json"
        meta = {"jql": "project = RHAIRFE", "fetched_at": time.time(), "total": 10}
        meta_path.write_text(json.dumps(meta))
        result = fetch_rfes.load_cache(meta_path, "project = RHAIRFE")
        assert result is not None
        assert result["total"] == 10

    def test_returns_none_for_invalid_json(self, tmp_path):
        meta_path = tmp_path / "_meta.json"
        meta_path.write_text("not json {{{")
        result = fetch_rfes.load_cache(meta_path, "project = RHAIRFE")
        assert result is None

    def test_just_within_ttl_is_valid(self, tmp_path):
        meta_path = tmp_path / "_meta.json"
        just_fresh = time.time() - (3.9 * 3600)  # 3.9 hours old, within 4h TTL
        meta = {"jql": "project = RHAIRFE", "fetched_at": just_fresh, "total": 7}
        meta_path.write_text(json.dumps(meta))
        result = fetch_rfes.load_cache(meta_path, "project = RHAIRFE")
        assert result is not None


class TestGetJiraConfig:
    def test_returns_error_when_all_env_vars_missing(self, monkeypatch):
        monkeypatch.delenv("JIRA_SERVER", raising=False)
        monkeypatch.delenv("JIRA_USER", raising=False)
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.setattr(fetch_rfes, "_load_jira_cli_config", lambda: (None, None))
        config, err = fetch_rfes.get_jira_config()
        assert config is None
        assert err is not None
        assert "Missing" in err

    def test_returns_error_when_only_token_missing(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://jira.example.com")
        monkeypatch.setenv("JIRA_USER", "user@example.com")
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        monkeypatch.setattr(fetch_rfes, "_load_jira_cli_config", lambda: (None, None))
        config, err = fetch_rfes.get_jira_config()
        assert config is None
        assert "JIRA_API_TOKEN" in err

    def test_returns_config_from_env_vars(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://jira.example.com")
        monkeypatch.setenv("JIRA_USER", "user@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "mytoken123")
        monkeypatch.setattr(fetch_rfes, "_load_jira_cli_config", lambda: (None, None))
        config, err = fetch_rfes.get_jira_config()
        assert err is None
        assert config["server"] == "https://jira.example.com"
        assert config["email"] == "user@example.com"
        assert config["token"] == "mytoken123"

    def test_strips_trailing_slash_from_server(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://jira.example.com/")
        monkeypatch.setenv("JIRA_USER", "user@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        monkeypatch.setattr(fetch_rfes, "_load_jira_cli_config", lambda: (None, None))
        config, err = fetch_rfes.get_jira_config()
        assert config["server"] == "https://jira.example.com"

    def test_env_vars_override_config_file(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://override.example.com")
        monkeypatch.setenv("JIRA_USER", "override@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")
        monkeypatch.setattr(
            fetch_rfes,
            "_load_jira_cli_config",
            lambda: ("https://file.example.com", "file@example.com"),
        )
        config, err = fetch_rfes.get_jira_config()
        assert config["server"] == "https://override.example.com"
        assert config["email"] == "override@example.com"
