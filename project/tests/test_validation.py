"""
Tests for input validation functions (EP 09, EP 12).
"""

from __future__ import annotations

import pytest

from src.models import ErrorCode, ToolError
from src.validation import (
    sanitize_string,
    validate_doc_id,
    validate_query,
    validate_ticket_input,
)


class TestSanitizeString:
    def test_normal_input(self) -> None:
        assert sanitize_string("Hello") == "Hello"

    def test_strips_whitespace(self) -> None:
        assert sanitize_string("  hi  ") == "hi"

    def test_truncates_to_max_length(self) -> None:
        result = sanitize_string("a" * 600, max_length=500)
        assert len(result) == 500

    def test_removes_control_chars(self) -> None:
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result

    def test_rejects_sql_injection(self) -> None:
        with pytest.raises(ToolError) as exc_info:
            sanitize_string("'; DROP TABLE users; --")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_rejects_xss(self) -> None:
        with pytest.raises(ToolError):
            sanitize_string("<script>alert(1)</script>")

    def test_rejects_nosql_injection(self) -> None:
        with pytest.raises(ToolError):
            sanitize_string("$gt")


class TestValidateTicketInput:
    def test_valid_input(self) -> None:
        result = validate_ticket_input("Server is down", "The server is completely unresponsive since morning", "high")
        assert result["title"] == "Server is down"
        assert result["priority"] == "high"

    @pytest.mark.parametrize("valid_priority", ["low", "medium", "high", "critical"])
    def test_valid_priorities(self, valid_priority: str) -> None:
        result = validate_ticket_input("Valid title", "Valid description here", valid_priority)
        assert result["priority"] == valid_priority

    @pytest.mark.parametrize("invalid_priority", ["urgent", "P1", "", "none"])
    def test_invalid_priorities(self, invalid_priority: str) -> None:
        with pytest.raises(ToolError) as exc_info:
            validate_ticket_input("Valid title", "Valid description here", invalid_priority)
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_short_title_rejected(self) -> None:
        with pytest.raises(ToolError):
            validate_ticket_input("Hi", "Valid description here", "medium")

    def test_short_description_rejected(self) -> None:
        with pytest.raises(ToolError):
            validate_ticket_input("Valid title", "Short", "medium")

    def test_long_title_truncated(self) -> None:
        result = validate_ticket_input("x" * 300, "Valid description here", "medium")
        assert len(result["title"]) == 200


class TestValidateQuery:
    def test_normal_query(self) -> None:
        assert validate_query("monitor") == "monitor"

    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ToolError):
            validate_query("")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ToolError):
            validate_query("   ")

    def test_respects_max_length(self) -> None:
        result = validate_query("a" * 200, max_length=100)
        assert len(result) == 100


class TestValidateDocId:
    @pytest.mark.parametrize("valid_id", ["remote-work", "vpn-setup", "a", "abc123"])
    def test_valid_doc_ids(self, valid_id: str) -> None:
        assert validate_doc_id(valid_id) == valid_id

    @pytest.mark.parametrize("malicious_id", [
        "../../../etc/passwd",
        "....//....//etc/passwd",
        "%2e%2e%2fetc%2fpasswd",
        "..\\..\\windows\\system32",
        "/etc/passwd",
        "remote-work\x00.md",
        "some.file.md",
        "foo/bar",
        "UPPERCASE",
    ])
    def test_path_traversal_blocked(self, malicious_id: str) -> None:
        with pytest.raises(ToolError) as exc_info:
            validate_doc_id(malicious_id)
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_empty_rejected(self) -> None:
        with pytest.raises(ToolError):
            validate_doc_id("")
