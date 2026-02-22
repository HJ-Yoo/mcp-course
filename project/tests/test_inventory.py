"""
Tests for inventory lookup logic and validation.

Tests the search/filtering behaviour and input validation
without spinning up the full MCP server.
"""

from __future__ import annotations

import pytest

from src.models import ErrorCode, InventoryItem, ToolError
from src.validation import sanitize_query


# ---------------------------------------------------------------------------
# Helper: mimics the core search logic from lookup_inventory
# ---------------------------------------------------------------------------

def search_inventory(items: list[InventoryItem], query: str) -> list[InventoryItem]:
    """Reproduce the search logic used by the lookup_inventory tool."""
    sanitized = sanitize_query(query)
    return [
        item
        for item in items
        if sanitized in item.name.lower() or sanitized in item.category.lower()
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInventorySearch:
    """Tests for the core inventory search logic."""

    def test_search_by_name(self, sample_inventory: list[InventoryItem]) -> None:
        """Searching by a substring of the item name returns matches."""
        results = search_inventory(sample_inventory, "Laptop")
        assert len(results) == 1
        assert results[0].item_id == "INV-001"

    def test_search_by_category(self, sample_inventory: list[InventoryItem]) -> None:
        """Searching by category returns all items in that category."""
        results = search_inventory(sample_inventory, "Electronics")
        assert len(results) == 2
        assert {r.item_id for r in results} == {"INV-001", "INV-003"}

    def test_search_case_insensitive(self, sample_inventory: list[InventoryItem]) -> None:
        """Search is case-insensitive."""
        results = search_inventory(sample_inventory, "CHAIR")
        assert len(results) == 1
        assert results[0].item_id == "INV-002"

    def test_search_no_results(self, sample_inventory: list[InventoryItem]) -> None:
        """Searching for a non-existent term returns an empty list."""
        results = search_inventory(sample_inventory, "Printer")
        assert len(results) == 0

    def test_empty_query_raises_tool_error(self) -> None:
        """An empty query string raises ToolError with INVALID_ARGUMENT."""
        with pytest.raises(ToolError) as exc_info:
            sanitize_query("")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_whitespace_only_query_raises_tool_error(self) -> None:
        """A whitespace-only query raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            sanitize_query("   ")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_query_with_extra_spaces(self, sample_inventory: list[InventoryItem]) -> None:
        """Extra spaces in query are collapsed before matching."""
        results = search_inventory(sample_inventory, "  office   chair  ")
        assert len(results) == 1
        assert results[0].item_id == "INV-002"
