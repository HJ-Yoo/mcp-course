"""
Tool: search_policy

Keyword search across policy markdown documents. Returns matching
doc_id, title, and a snippet from the first matching section.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context

from src.audit import AuditLogger
from src.models import AppContext
from src.validation import sanitize_query

SNIPPET_LENGTH = 200


def register(mcp) -> None:
    """Register the search_policy tool on the MCP server."""

    @mcp.tool()
    async def search_policy(query: str, ctx: Context) -> str:
        """Search policy documents by keyword.

        Performs a case-insensitive keyword search across all policy
        markdown files. Returns matching documents with a short snippet
        from the first matching section.

        Args:
            query: Keyword(s) to search for within policy documents.
            ctx: MCP request context (injected automatically).

        Returns:
            JSON array of matching policies with snippets, or a message
            if none found.
        """
        app: AppContext = ctx.request_context.lifespan_context["app"]
        logger = AuditLogger(app.audit_log_path)

        sanitized = sanitize_query(query)

        results: list[dict] = []
        for doc in app.policies:
            if not doc.path.exists():
                continue

            content = doc.path.read_text(encoding="utf-8")
            content_lower = content.lower()

            if sanitized in content_lower:
                # Find the position of the match and extract a snippet
                match_pos = content_lower.index(sanitized)
                # Start a bit before the match for context
                start = max(0, match_pos - 40)
                snippet = content[start : start + SNIPPET_LENGTH].strip()
                # Replace newlines with spaces for a cleaner snippet
                snippet = " ".join(snippet.split())

                results.append(
                    {
                        "doc_id": doc.doc_id,
                        "title": doc.title,
                        "snippet": snippet,
                    }
                )

        if not results:
            message = f"No policies found matching '{sanitized}'"
            logger.log(
                action="search",
                tool_name="search_policy",
                input_summary=f"query={sanitized}",
                result_summary=message,
                success=True,
            )
            return message

        result_json = json.dumps(results, ensure_ascii=False, indent=2)

        logger.log(
            action="search",
            tool_name="search_policy",
            input_summary=f"query={sanitized}",
            result_summary=f"Found {len(results)} matching policy/policies",
            success=True,
        )
        return result_json
