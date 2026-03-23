"""
Tests for AuditLogger (EP 14).
"""

from __future__ import annotations

import json

import pytest

from src.audit import AuditLogger


class TestAuditLogger:
    async def test_log_entry_format(self, audit_logger: AuditLogger) -> None:
        """Log entry should contain all expected fields."""
        await audit_logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            input_summary={"query": "monitor"},
            success=True,
            duration_ms=12.45,
        )
        content = audit_logger.log_path.read_text()
        entry = json.loads(content.strip())

        assert entry["tool_name"] == "lookup_inventory"
        assert entry["success"] is True
        assert entry["duration_ms"] == 12.45
        assert "timestamp" in entry

    async def test_log_path_property(self, audit_logger: AuditLogger) -> None:
        """log_path should point to audit.jsonl inside log_dir."""
        assert audit_logger.log_path.name == "audit.jsonl"

    def test_start_timer_and_elapsed(self, audit_logger: AuditLogger) -> None:
        """start_timer / elapsed_ms should return positive values."""
        start = audit_logger.start_timer()
        elapsed = audit_logger.elapsed_ms(start)
        assert elapsed >= 0

    async def test_multiple_entries_append(self, audit_logger: AuditLogger) -> None:
        """Multiple log calls should produce multiple JSONL lines."""
        await audit_logger.log(action="call_1", tool_name="tool_a", success=True)
        await audit_logger.log(action="call_2", tool_name="tool_b", success=False)

        lines = audit_logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        assert entry1["tool_name"] == "tool_a"
        assert entry2["success"] is False
