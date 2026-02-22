"""
Tool: create_ticket

Creates support tickets with a two-step confirm flow and idempotency support.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from mcp.server.fastmcp import Context

from src.audit import AuditLogger
from src.models import AppContext, Ticket
from src.validation import validate_priority, validate_text_length


def register(mcp) -> None:
    """Register the create_ticket tool on the MCP server."""

    @mcp.tool()
    async def create_ticket(
        title: str,
        body: str,
        priority: str,
        confirm: bool = False,
        idempotency_key: str | None = None,
        ctx: Context = None,
    ) -> str:
        """Create a new support ticket.

        Uses a two-step confirmation flow: first call with confirm=False
        returns a preview, then call again with confirm=True to actually
        create the ticket.

        Supports idempotency: if an idempotency_key is provided and matches
        an existing ticket, the existing ticket is returned instead of
        creating a duplicate.

        Args:
            title: Short summary of the issue (max 200 chars).
            body: Detailed description (max 500 chars).
            priority: One of 'low', 'medium', 'high', 'critical'.
            confirm: Set to True to actually create the ticket.
            idempotency_key: Optional unique key to prevent duplicate creation.
            ctx: MCP request context (injected automatically).

        Returns:
            Preview text (if confirm=False) or JSON of the created ticket.
        """
        app: AppContext = ctx.request_context.lifespan_context["app"]
        logger = AuditLogger(app.audit_log_path)

        # Validate inputs
        validated_priority = validate_priority(priority)
        validated_title = validate_text_length(title, "title", max_len=200)
        validated_body = validate_text_length(body, "body", max_len=500)

        # Preview mode
        if not confirm:
            preview = (
                f"Preview: Ticket '{validated_title}' (priority: {validated_priority}). "
                f"Set confirm=True to create."
            )
            logger.log(
                action="preview",
                tool_name="create_ticket",
                input_summary=f"title={validated_title}, priority={validated_priority}",
                result_summary="Preview returned",
                success=True,
            )
            return preview

        # Idempotency check
        if idempotency_key:
            existing_tickets = app.load_tickets()
            for ticket in existing_tickets:
                if ticket.idempotency_key == idempotency_key:
                    result_json = json.dumps(asdict(ticket), ensure_ascii=False, indent=2)
                    logger.log(
                        action="idempotent_return",
                        tool_name="create_ticket",
                        input_summary=f"idempotency_key={idempotency_key}",
                        result_summary=f"Returned existing ticket {ticket.ticket_id}",
                        success=True,
                    )
                    return result_json

        # Create the ticket
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

        result_json = json.dumps(asdict(ticket), ensure_ascii=False, indent=2)

        logger.log(
            action="create",
            tool_name="create_ticket",
            input_summary=f"title={validated_title}, priority={validated_priority}",
            result_summary=f"Created ticket {ticket_id}",
            success=True,
        )
        return result_json
