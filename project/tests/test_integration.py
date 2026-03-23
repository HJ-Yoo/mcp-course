"""
Integration tests — full workflow scenarios (EP 16).
"""

from __future__ import annotations

import json

import pytest

from src.models import AppContext, Ticket


class TestInventoryWorkflow:
    """Search inventory via SQL DB."""

    def test_search_and_find_items(self, app_context: AppContext) -> None:
        rows = app_context.db.execute(
            "SELECT * FROM inventory WHERE LOWER(name) LIKE ?",
            ("%laptop%",),
        ).fetchall()
        assert len(rows) >= 1
        assert any("Laptop" in dict(r)["name"] for r in rows)

    def test_search_no_results(self, app_context: AppContext) -> None:
        rows = app_context.db.execute(
            "SELECT * FROM inventory WHERE LOWER(name) LIKE ?",
            ("%spaceship%",),
        ).fetchall()
        assert len(rows) == 0


class TestTicketCreationWorkflow:
    """Create and persist tickets via JSONL."""

    def test_create_and_persist(self, app_context: AppContext) -> None:
        ticket = Ticket(
            ticket_id="TKT-100",
            title="프린터 수리 요청",
            priority="high",
            body="3층 프린터가 작동하지 않습니다.",
            status="open",
            created_at="2026-01-15T09:00:00",
        )
        app_context.append_ticket(ticket)

        tickets = app_context.load_tickets()
        assert len(tickets) == 1
        assert tickets[0].ticket_id == "TKT-100"
        assert tickets[0].title == "프린터 수리 요청"


class TestEndToEndScenario:
    """Full workflow: search → policy → ticket → audit log."""

    async def test_full_workflow(self, app_context: AppContext) -> None:
        logger = app_context.audit_logger

        # Step 1: 재고 검색
        rows = app_context.db.execute(
            "SELECT * FROM inventory WHERE LOWER(category) LIKE ?",
            ("%electronics%",),
        ).fetchall()
        assert len(rows) >= 1
        await logger.log(
            action="tool_call",
            tool_name="lookup_inventory",
            success=True,
        )

        # Step 2: 정책 확인
        policy = next(
            (p for p in app_context.policies if p.doc_id == "remote-work"),
            None,
        )
        assert policy is not None

        # Step 3: 티켓 생성 + 로그 확인
        await logger.log(
            action="tool_call",
            tool_name="create_ticket",
            success=True,
        )

        lines = logger.log_path.read_text().strip().split("\n")
        assert len(lines) == 2
