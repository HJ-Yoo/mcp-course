"""
TODO (Episode 15): Test policy resources.

테스트 구조:
  1. build_policy_index 헬퍼 — policy://index 로직 재현
  2. get_policy_content 헬퍼 — policy://{doc_id} 로직 재현
  3. TestPolicyIndex — 정책 목록 테스트
  4. TestPolicyDetail — 정책 상세 + 경로 순회 방어 테스트

conftest.py의 sample_policies fixture가 자동 주입됩니다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import AppContext, ErrorCode, PolicyDoc, ToolError
from src.validation import validate_doc_id


# ---------------------------------------------------------------------------
# Helper: policy://index 로직 재현
# ---------------------------------------------------------------------------

def build_policy_index(policies: list[PolicyDoc]) -> list[dict]:
    """policy://index Resource의 로직을 재현."""
    # TODO:
    #   각 PolicyDoc에서 doc_id, title, tags를 추출하여
    #   dict 리스트로 반환
    pass


# ---------------------------------------------------------------------------
# Helper: policy://{doc_id} 로직 재현
# ---------------------------------------------------------------------------

def get_policy_content(policies: list[PolicyDoc], doc_id: str) -> dict:
    """policy://{doc_id} Resource의 로직을 재현."""
    # TODO:
    #   1. validate_doc_id(doc_id)
    #   2. policies에서 doc_id가 일치하는 PolicyDoc 찾기
    #   3. 없으면 ToolError(ErrorCode.NOT_FOUND, ...) raise
    #   4. path.read_text()로 내용 읽기
    #   5. {"doc_id": ..., "title": ..., "content": ...} 반환
    pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPolicyIndex:
    """정책 목록 테스트."""

    def test_index_returns_all_policies(self, sample_policies: list[PolicyDoc]) -> None:
        """인덱스에 등록된 모든 정책이 포함된다."""
        # TODO: build_policy_index(sample_policies)
        #       assert len(index) == 2
        #       doc_ids = {entry["doc_id"] for entry in index}
        #       assert doc_ids == {"remote-work", "security-guidelines"}
        pass

    def test_index_contains_expected_fields(self, sample_policies: list[PolicyDoc]) -> None:
        """각 엔트리에 doc_id, title, tags 필드가 있다."""
        # TODO: build_policy_index 후 각 entry에 필드 존재 확인
        pass

    def test_index_serializes_to_json(self, sample_policies: list[PolicyDoc]) -> None:
        """인덱스가 유효한 JSON으로 직렬화된다."""
        # TODO: json.dumps → json.loads → len 확인
        pass


class TestPolicyDetail:
    """정책 상세 조회 + 경로 순회 방어 테스트."""

    def test_detail_returns_content(self, sample_policies: list[PolicyDoc]) -> None:
        """유효한 doc_id로 조회 시 doc_id, title, content가 반환된다."""
        # TODO: get_policy_content(sample_policies, "remote-work")
        #       assert result["doc_id"] == "remote-work"
        #       assert result["title"] == "재택근무 정책"
        #       assert "자격 요건" in result["content"]
        pass

    def test_detail_not_found(self, sample_policies: list[PolicyDoc]) -> None:
        """존재하지 않는 doc_id는 ToolError(NOT_FOUND)를 발생시킨다."""
        # TODO: pytest.raises(ToolError), ErrorCode.NOT_FOUND 확인
        pass

    def test_path_traversal_raises_error(self, sample_policies: list[PolicyDoc]) -> None:
        """경로 순회 공격(../)은 ToolError(INVALID_ARGUMENT)를 발생시킨다."""
        # TODO: get_policy_content(sample_policies, "../etc/passwd")
        pass

    def test_path_traversal_with_dots(self, sample_policies: list[PolicyDoc]) -> None:
        """점(.)이 포함된 doc_id는 거부된다."""
        # TODO: get_policy_content(sample_policies, "some.file.md")
        pass

    def test_path_traversal_with_slashes(self, sample_policies: list[PolicyDoc]) -> None:
        """슬래시(/)가 포함된 doc_id는 거부된다."""
        # TODO: get_policy_content(sample_policies, "foo/bar")
        pass
