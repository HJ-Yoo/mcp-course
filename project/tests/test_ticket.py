"""
Tests for ticket creation logic: preview mode, creation,
idempotency, and validation.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

import pytest

from src.audit import AuditLogger
from src.models import AppContext, ErrorCode, Ticket, ToolError
from src.validation import validate_ticket_input


# ---------------------------------------------------------------------------
# Helpers: mimic the core create_ticket logic without MCP context
# ---------------------------------------------------------------------------

def preview_ticket(title: str, body: str, priority: str) -> str:
    """Reproduce the preview logic of create_ticket (confirm=False)."""
    validated = validate_ticket_input(title, body, priority)
    return (
        f"Preview: Ticket '{validated['title']}' (priority: {validated['priority']}). "
        f"Set confirm=True to create."
    )


def create_ticket_logic(
    app: AppContext,
    title: str,
    body: str,
    priority: str,
    idempotency_key: str | None = None,
) -> dict:
    """Reproduce the creation logic of create_ticket (confirm=True)."""
    validated = validate_ticket_input(title, body, priority)
    validated_title = validated["title"]
    validated_body = validated["description"]
    validated_priority = validated["priority"]

    # Idempotency check
    if idempotency_key:
        existing_tickets = app.load_tickets()
        for ticket in existing_tickets:
            if ticket.idempotency_key == idempotency_key:
                return asdict(ticket)

    ticket_id = app.next_ticket_id()
    now = datetime.now(timezone.utc).isoformat()

    ticket = Ticket(
        ticket_id=ticket_id,
        title=validated_title,
        priority=validated_priority,
        body=validated_body,
        status="open",
        created_at=now,
        idempotency_key=idempotency_key,
    )

    app.append_ticket(ticket)
    return asdict(ticket)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTicketPreview:
    """Tests for the ticket preview flow (confirm=False)."""

    def test_preview_returns_summary(self) -> None:
        """Preview mode returns a human-readable summary with the title and priority."""
        result = preview_ticket("Server is down", "The server is completely unresponsive", "high")
        assert "Preview:" in result
        assert "Server is down" in result
        assert "high" in result
        assert "confirm=True" in result

    def test_preview_normalizes_priority(self) -> None:
        """Preview normalizes priority to lowercase."""
        result = preview_ticket("Test issue here", "This is a test issue description", "HIGH")
        assert "high" in result


class TestTicketCreation:
    """Tests for actual ticket creation (confirm=True)."""

    def test_create_ticket_returns_ticket_data(self, app_context: AppContext) -> None:
        """Creating a ticket returns a dict with all expected fields."""
        result = create_ticket_logic(
            app_context,
            title="Broken printer",
            body="The office printer on floor 3 is jammed.",
            priority="medium",
        )
        assert result["ticket_id"].startswith("TKT-")
        assert result["title"] == "Broken printer"
        assert result["priority"] == "medium"
        assert result["status"] == "open"
        assert result["body"] == "The office printer on floor 3 is jammed."

    def test_create_ticket_persists(self, app_context: AppContext) -> None:
        """Created tickets are persisted and can be loaded back."""
        create_ticket_logic(
            app_context,
            title="Need new monitor",
            body="My monitor is flickering.",
            priority="low",
        )
        tickets = app_context.load_tickets()
        assert len(tickets) == 1
        assert tickets[0].title == "Need new monitor"

    def test_sequential_ticket_ids(self, app_context: AppContext) -> None:
        """Successive ticket creations produce incrementing IDs."""
        t1 = create_ticket_logic(app_context, "First", "Body one", "low")
        t2 = create_ticket_logic(app_context, "Second", "Body two", "medium")

        id1 = int(t1["ticket_id"].split("-")[1])
        id2 = int(t2["ticket_id"].split("-")[1])
        assert id2 == id1 + 1


class TestTicketIdempotency:
    """Tests for idempotent ticket creation."""

    def test_idempotent_create_returns_same_ticket(self, app_context: AppContext) -> None:
        """Using the same idempotency key returns the original ticket."""
        key = "unique-key-123"

        first = create_ticket_logic(
            app_context,
            title="Duplicate test",
            body="Testing idempotency.",
            priority="high",
            idempotency_key=key,
        )

        second = create_ticket_logic(
            app_context,
            title="Duplicate test",
            body="Testing idempotency.",
            priority="high",
            idempotency_key=key,
        )

        assert first["ticket_id"] == second["ticket_id"]

    def test_different_keys_create_different_tickets(self, app_context: AppContext) -> None:
        """Different idempotency keys create separate tickets."""
        t1 = create_ticket_logic(
            app_context, "Issue A", "Body A", "low", idempotency_key="key-a"
        )
        t2 = create_ticket_logic(
            app_context, "Issue B", "Body B", "low", idempotency_key="key-b"
        )
        assert t1["ticket_id"] != t2["ticket_id"]

    def test_no_key_always_creates_new(self, app_context: AppContext) -> None:
        """Without an idempotency key, each call creates a new ticket."""
        t1 = create_ticket_logic(app_context, "Issue X", "Body X", "low")
        t2 = create_ticket_logic(app_context, "Issue X", "Body X", "low")
        assert t1["ticket_id"] != t2["ticket_id"]


class TestTicketValidation:
    """Tests for input validation in ticket creation."""

    def test_invalid_priority_raises_error(self) -> None:
        """An invalid priority value raises ToolError with INVALID_ARGUMENT."""
        with pytest.raises(ToolError) as exc_info:
            validate_ticket_input("Valid title", "Valid description here", "urgent")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_empty_title_raises_error(self) -> None:
        """An empty title raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            validate_ticket_input("", "Valid description here", "medium")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_short_title_raises_error(self) -> None:
        """A title shorter than 5 chars raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            validate_ticket_input("Hi", "Valid description here", "medium")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_short_description_raises_error(self) -> None:
        """A description shorter than 10 chars raises ToolError."""
        with pytest.raises(ToolError) as exc_info:
            validate_ticket_input("Valid title", "Short", "medium")
        assert exc_info.value.code == ErrorCode.INVALID_ARGUMENT

    def test_long_title_truncated(self) -> None:
        """A title exceeding max length is truncated by sanitize_string."""
        long_title = "x" * 300
        result = validate_ticket_input(long_title, "Valid description here", "medium")
        assert len(result["title"]) == 200
