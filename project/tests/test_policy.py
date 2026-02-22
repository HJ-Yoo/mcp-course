"""
Tests for policy resources: index listing, content retrieval,
and path traversal prevention.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import AppContext, ErrorCode, PolicyDoc, ToolError
from src.validation import validate_doc_id


# ---------------------------------------------------------------------------
# Helper: mimics policy_index logic
# ---------------------------------------------------------------------------

def build_policy_index(policies: list[PolicyDoc]) -> list[dict]:
    """Reproduce the logic of the policy://index resource."""
    return [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "tags": doc.tags,
        }
        for doc in policies
    ]


def get_policy_content(policies: list[PolicyDoc], doc_id: str) -> str:
    """Reproduce the logic of the policy://{doc_id} resource."""
    validated_id = validate_doc_id(doc_id)
    for doc in policies:
        if doc.doc_id == validated_id:
            if not doc.path.exists():
                raise ToolError(
                    ErrorCode.NOT_FOUND,
                    f"Policy file for '{validated_id}' not found on disk.",
                )
            return doc.path.read_text(encoding="utf-8")
    raise ToolError(
        ErrorCode.NOT_FOUND,
        f"No policy document found with ID '{validated_id}'.",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPolicyIndex:
    """Tests for the policy index resource."""

    def test_index_returns_all_policies(self, sample_policies: list[PolicyDoc]) -> None:
        """The index should contain all registered policies."""
        index = build_policy_index(sample_policies)
        assert len(index) == 2

        doc_ids = {entry["doc_id"] for entry in index}
        assert doc_ids == {"remote-work", "security-guidelines"}

    def test_index_contains_expected_fields(self, sample_policies: list[PolicyDoc]) -> None:
        """Each entry in the index has doc_id, title, and tags."""
        index = build_policy_index(sample_policies)
        for entry in index:
            assert "doc_id" in entry
            assert "title" in entry
            assert "tags" in entry
            assert isinstance(entry["tags"], list)

    def test_index_serializes_to_json(self, sample_policies: list[PolicyDoc]) -> None:
        """The index can be serialized to valid JSON."""
        index = build_policy_index(sample_policies)
        json_str = json.dumps(index)
        parsed = json.loads(json_str)
        assert len(parsed) == 2


class TestPolicyDetail:
    """Tests for the policy detail resource."""

    def test_detail_returns_content(self, sample_policies: list[PolicyDoc]) -> None:
        """Retrieving a valid doc_id returns its markdown content."""
        content = get_policy_content(sample_policies, "remote-work")
        assert "Remote Work Policy" in content
        assert "Eligibility" in content

    def test_detail_not_found(self, sample_policies: list[PolicyDoc]) -> None:
        """Requesting a non-existent doc_id raises ToolError NOT_FOUND."""
        with pytest.raises(ToolError) as exc_info:
            get_policy_content(sample_policies, "nonexistent-policy")
        assert exc_info.value.code == ErrorCode.NOT_FOUND

    def test_path_traversal_raises_error(self, sample_policies: list[PolicyDoc]) -> None:
        """Attempting path traversal (../) in doc_id raises INVALID_ARGUMENT."""
        with pytest.raises(ToolError) as exc_info:
            get_policy_content(sample_policies, "../etc/passwd")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_path_traversal_with_dots(self, sample_policies: list[PolicyDoc]) -> None:
        """Doc IDs containing dots are rejected."""
        with pytest.raises(ToolError) as exc_info:
            get_policy_content(sample_policies, "some.file.md")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_path_traversal_with_slashes(self, sample_policies: list[PolicyDoc]) -> None:
        """Doc IDs containing slashes are rejected."""
        with pytest.raises(ToolError) as exc_info:
            get_policy_content(sample_policies, "foo/bar")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT
