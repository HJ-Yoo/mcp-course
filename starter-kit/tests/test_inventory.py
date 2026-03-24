"""
TODO (Episode 15): Test inventory lookup.

테스트 구조:
  1. search_inventory_db 헬퍼 — 실제 lookup_inventory 로직 재현
  2. TestInventorySearch 클래스 — DB 기반 검색 테스트

conftest.py의 sample_db fixture가 자동 주입됩니다.
"""
from __future__ import annotations

import re
import sqlite3

import pytest

from src.models import ErrorCode, ToolError
from src.validation import validate_query


# ---------------------------------------------------------------------------
# Helper: lookup_inventory의 핵심 검색 로직 재현
# ---------------------------------------------------------------------------

def search_inventory_db(db: sqlite3.Connection, query: str) -> list[dict]:
    """lookup_inventory Tool의 검색 로직을 재현."""
    # TODO:
    #   1. validate_query(query)
    #   2. re.sub(r"\s+", " ", validated).lower()  → 공백 정리 + 소문자
    #   3. like_pattern = f"%{sanitized}%"
    #   4. SQL: SELECT ... FROM inventory
    #          WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?
    #          LIMIT 10
    #   5. return [dict(row) for row in rows]
    pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInventorySearch:
    """재고 검색 로직 테스트."""

    def test_search_by_name(self, sample_db: sqlite3.Connection) -> None:
        """이름 부분 문자열로 검색하면 해당 아이템이 반환된다."""
        # TODO: search_inventory_db(sample_db, "Laptop")
        #       assert len(results) == 1
        #       assert results[0]["item_id"] == "INV-001"
        pass

    def test_search_by_category(self, sample_db: sqlite3.Connection) -> None:
        """카테고리로 검색하면 해당 카테고리의 모든 아이템이 반환된다."""
        # TODO: search_inventory_db(sample_db, "Electronics")
        #       assert len(results) == 2
        pass

    def test_search_case_insensitive(self, sample_db: sqlite3.Connection) -> None:
        """대소문자 구분 없이 검색된다."""
        # TODO: search_inventory_db(sample_db, "CHAIR")
        #       assert len(results) == 1
        pass

    def test_search_no_results(self, sample_db: sqlite3.Connection) -> None:
        """존재하지 않는 검색어는 빈 리스트를 반환한다."""
        # TODO: search_inventory_db(sample_db, "Printer")
        #       assert len(results) == 0
        pass

    def test_empty_query_raises_tool_error(self) -> None:
        """빈 쿼리는 ToolError(INVALID_ARGUMENT)를 발생시킨다."""
        # TODO: with pytest.raises(ToolError) as exc_info:
        #           validate_query("")
        #       assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT
        pass

    def test_query_with_extra_spaces(self, sample_db: sqlite3.Connection) -> None:
        """쿼리의 여분 공백이 정리된 후 검색된다."""
        # TODO: search_inventory_db(sample_db, "  office   chair  ")
        #       assert len(results) == 1
        pass
