"""
Tool: lookup_inventory

Searches the inventory by name or category using SQL LIKE pattern matching.
"""

from __future__ import annotations

import json
import re

from mcp.server.fastmcp import Context

from src.audit import AuditLogger
from src.models import AppContext
from src.validation import validate_query

MAX_RESULTS = 10


def register(mcp) -> None:
    """Register the lookup_inventory tool on the MCP server."""

    @mcp.tool()
    async def lookup_inventory(query: str, ctx: Context) -> str:
        """Search inventory items by name or category.

        Performs a case-insensitive substring match against item names
        and categories using SQL LIKE. Returns up to 10 matching items as JSON.

        Args:
            query: Search term to match against item name or category.
            ctx: MCP request context (injected automatically).

        Returns:
            JSON array of matching inventory items, or a message if none found.
        """
        app: AppContext = ctx.request_context.lifespan_context["app"]
        logger = AuditLogger(app.audit_log_path)

        validated = validate_query(query, min_length=1, max_length=100)
        sanitized = re.sub(r"\s+", " ", validated).lower()
        like_pattern = f"%{sanitized}%"

        rows = app.db.execute(
            """SELECT item_id, name, category, quantity,
                      location, status, last_updated
               FROM inventory
               WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ?
               LIMIT ?""",
            (like_pattern, like_pattern, MAX_RESULTS),
        ).fetchall()

        if not rows:
            result = f"No items found matching '{sanitized}'"
            logger.log(
                action="lookup",
                tool_name="lookup_inventory",
                input_summary=f"query={sanitized}",
                result_summary=result,
                success=True,
            )
            return result

        result_json = json.dumps(
            [dict(row) for row in rows],
            ensure_ascii=False,
            indent=2,
        )

        logger.log(
            action="lookup",
            tool_name="lookup_inventory",
            input_summary=f"query={sanitized}",
            result_summary=f"Found {len(rows)} item(s)",
            success=True,
        )
        return result_json
