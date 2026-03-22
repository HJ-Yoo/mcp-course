"""
Tests for inventory lookup logic and validation.

Tests the search/filtering behaviour and input validation
without spinning up the full MCP server.
"""

from __future__ import annotations

import re
import sqlite3

import pytest

from src.models import ErrorCode, ToolError
from src.validation import validate_query


# ---------------------------------------------------------------------------
# Helper: mimics the core search logic from lookup_inventory (SQL LIKE)
# ---------------------------------------------------------------------------

def search_inventory_db(db: sqlite3.Connection, query: str) -> list[dict]:
    """Reproduce the search logic used by the lookup_inventory tool."""
    validated = validate_query(query)
    sanitized = re.sub(r"\s+", " ", validated).lower()
    like_pattern = f"%{sanitized}%"
    rows = db.execute(
        """SELECT item_id, name, category, quantity,
                  location, status, last_updated
           FROM inventory
           WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?
           LIMIT 10""",
        (like_pattern, like_pattern),
    ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInventorySearch:
    """Tests for the core inventory search logic."""

    def test_search_by_name(self, sample_db: sqlite3.Connection) -> None:
        """Searching by a substring of the item name returns matches."""
        results = search_inventory_db(sample_db, "Laptop")
        assert len(results) == 1
        assert results[0]["item_id"] == "INV-001"

    def test_search_by_category(self, sample_db: sqlite3.Connection) -> None:
        """Searching by category returns all items in that category."""
        results = search_inventory_db(sample_db, "Electronics")
        assert len(results) == 2
        assert {r["item_id"] for r in results} == {"INV-001", "INV-003"}

    def test_search_case_insensitive(self, sample_db: sqlite3.Connection) -> None:
        """Search is case-insensitive."""
        results = search_inventory_db(sample_db, "CHAIR")
        assert len(results) == 1
        assert results[0]["item_id"] == "INV-002"

    def test_search_no_results(self, sample_db: sqlite3.Connection) -> None:
        """Searching for a non-existent term returns an empty list."""
        results = search_inventory_db(sample_db, "Printer")
        assert len(results) == 0

    def test_empty_query_raises_tool_error(self) -> None:
        """An empty query string raises ToolError with INVALID_ARGUMENT."""
        with pytest.raises(ToolError) as exc_info:
            validate_query("")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_whitespace_only_query_raises_tool_error(self) -> None:
        """A whitespace-only query raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            validate_query("   ")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_query_with_extra_spaces(self, sample_db: sqlite3.Connection) -> None:
        """Extra spaces in query are collapsed before matching."""
        results = search_inventory_db(sample_db, "  office   chair  ")
        assert len(results) == 1
        assert results[0]["item_id"] == "INV-002"
