"""
TODO (Episode 15): 입력 검증 단위 테스트.

슬라이드에서 다룬 패턴:
  - @pytest.mark.parametrize로 여러 입력 테스트
  - pytest.raises로 예외 검증
"""
from __future__ import annotations

import pytest


class TestValidateTicketInput:
    """validate_ticket_input 테스트."""

    # TODO: from src.validation import validate_ticket_input

    @pytest.mark.parametrize("valid_priority", ["low", "medium", "high", "critical"])
    def test_valid_priorities(self, valid_priority: str) -> None:
        # TODO: validate_ticket_input 호출, result["priority"] 확인
        pass

    @pytest.mark.parametrize("invalid_priority", ["urgent", "P1", "", "none"])
    def test_invalid_priorities(self, invalid_priority: str) -> None:
        # TODO: pytest.raises(ToolError)로 예외 확인
        pass

    def test_short_title_rejected(self) -> None:
        # TODO: 5자 미만 제목 → ToolError
        pass

    def test_short_description_rejected(self) -> None:
        # TODO: 10자 미만 설명 → ToolError
        pass


class TestValidateDocId:
    """validate_doc_id 보안 테스트."""

    # TODO: from src.validation import validate_doc_id

    @pytest.mark.parametrize("malicious_id", [
        "../../../etc/passwd",
        "....//....//etc/passwd",
        "%2e%2e%2fetc%2fpasswd",
        "..\\..\\windows\\system32",
        "/etc/passwd",
        "remote-work\x00.md",
    ])
    def test_path_traversal_blocked(self, malicious_id: str) -> None:
        # TODO: pytest.raises(ToolError)로 모든 공격 패턴 차단 확인
        pass
