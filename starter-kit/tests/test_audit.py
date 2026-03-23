"""
TODO (Episode 15): AuditLogger 단위 테스트.

슬라이드에서 다룬 패턴:
  - async 테스트 (asyncio_mode = "auto")
  - JSONL 포맷 검증

conftest.py에 audit_logger fixture를 먼저 구현한 후 테스트를 작성하세요.
"""
from __future__ import annotations

# TODO: import json, pytest
# TODO: from src.audit import AuditLogger


# TODO: class TestAuditLogger:
#
#     async def test_log_entry_format(self, audit_logger) -> None:
#         """로그 엔트리에 올바른 필드가 포함되는지 확인."""
#         # await audit_logger.log(...)
#         # audit_logger.log_path.read_text()로 내용 읽기
#         # json.loads()로 파싱
#         # assert entry["tool_name"] == "lookup_inventory"
#         pass
#
#     async def test_multiple_entries_append(self, audit_logger) -> None:
#         """여러 번 log 호출 시 JSONL 라인이 추가되는지 확인."""
#         # 2번 log 호출 후 라인 수가 2인지 확인
#         pass
