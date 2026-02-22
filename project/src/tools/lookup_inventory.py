"""
Tool: lookup_inventory

Searches the inventory by name or category using fuzzy substring matching.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from mcp.server.fastmcp import Context

from src.audit import AuditLogger
from src.models import AppContext
from src.validation import sanitize_query

MAX_RESULTS = 10


def register(mcp) -> None:
    """Register the lookup_inventory tool on the MCP server."""

    @mcp.tool()
    async def lookup_inventory(query: str, ctx: Context) -> str:
        """Search inventory items by name or category.

        Performs a case-insensitive substring match against item names
        and categories. Returns up to 10 matching items as JSON.

        Args:
            query: Search term to match against item name or category.
            ctx: MCP request context (injected automatically).

        Returns:
            JSON array of matching inventory items, or a message if none found.
        """
        app: AppContext = ctx.request_context.lifespan_context["app"]
        logger = AuditLogger(app.audit_log_path)

        sanitized = sanitize_query(query)

        matches = [
            item
            for item in app.inventory
            if sanitized in item.name.lower() or sanitized in item.category.lower()
        ]

        if not matches:
            result = f"No items found matching '{sanitized}'"
            logger.log(
                action="lookup",
                tool_name="lookup_inventory",
                input_summary=f"query={sanitized}",
                result_summary=result,
                success=True,
            )
            return result

        limited = matches[:MAX_RESULTS]
        result_json = json.dumps(
            [asdict(item) for item in limited],
            ensure_ascii=False,
            indent=2,
        )

        logger.log(
            action="lookup",
            tool_name="lookup_inventory",
            input_summary=f"query={sanitized}",
            result_summary=f"Found {len(limited)} item(s)",
            success=True,
        )
        return result_json
