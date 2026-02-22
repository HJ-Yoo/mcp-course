"""
Resources: policy

Exposes policy documents as MCP resources:
- policy://index  — list of all available policies
- policy://{doc_id} — full markdown content of a specific policy
"""

from __future__ import annotations

import json

from src.models import AppContext, ErrorCode, ToolError
from src.validation import validate_doc_id


def register(mcp) -> None:
    """Register policy resources on the MCP server."""

    @mcp.resource("policy://index")
    async def policy_index() -> str:
        """List all available policy documents.

        Returns a JSON array containing the doc_id, title, and tags
        for every registered policy document.
        """
        ctx = mcp.get_context()
        app: AppContext = ctx.request_context.lifespan_context["app"]

        index = [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "tags": doc.tags,
            }
            for doc in app.policies
        ]
        return json.dumps(index, ensure_ascii=False, indent=2)

    @mcp.resource("policy://{doc_id}")
    async def policy_detail(doc_id: str) -> str:
        """Retrieve the full markdown content of a specific policy document.

        Args:
            doc_id: The identifier of the policy document (alphanumeric and hyphens only).

        Returns:
            The full markdown content of the policy.

        Raises:
            ToolError: If the doc_id is invalid or the document is not found.
        """
        validated_id = validate_doc_id(doc_id)

        ctx = mcp.get_context()
        app: AppContext = ctx.request_context.lifespan_context["app"]

        for doc in app.policies:
            if doc.doc_id == validated_id:
                if not doc.path.exists():
                    raise ToolError(
                        ErrorCode.NOT_FOUND,
                        f"Policy file for '{validated_id}' not found on disk.",
                    )
                return doc.path.read_text(encoding="utf-8")

        raise ToolError(
            ErrorCode.NOT_FOUND,
            f"No policy document found with ID '{validated_id}'.",
        )
