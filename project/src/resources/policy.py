"""
Resources: policy

Exposes policy documents as MCP resources:
- policy://index  — list of all available policies (JSON)
- policy://{doc_id} — full content of a specific policy (JSON)
"""

from __future__ import annotations

import json

from src.models import AppContext, ErrorCode, ToolError
from src.validation import validate_doc_id


def register(mcp) -> None:
    """Register policy resources on the MCP server."""

    @mcp.resource("policy://index", mime_type="application/json")
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

    @mcp.resource("policy://{doc_id}", mime_type="application/json")
    async def policy_detail(doc_id: str) -> str:
        """Retrieve the full content of a specific policy document.

        Args:
            doc_id: The identifier of the policy document (lowercase alphanumeric and hyphens only).

        Returns:
            JSON containing doc_id, title, and full content of the policy.

        Raises:
            ToolError: If the doc_id is invalid or the document is not found.
        """
        validated_id = validate_doc_id(doc_id)

        ctx = mcp.get_context()
        app: AppContext = ctx.request_context.lifespan_context["app"]

        policy = next(
            (p for p in app.policies if p.doc_id == validated_id),
            None,
        )
        if policy is None:
            raise ToolError(
                ErrorCode.NOT_FOUND,
                f"No policy document found with ID '{validated_id}'.",
            )
        if not policy.path.exists():
            raise ToolError(
                ErrorCode.NOT_FOUND,
                f"Policy file for '{validated_id}' not found on disk.",
            )

        content = policy.path.read_text(encoding="utf-8")
        return json.dumps({
            "doc_id": policy.doc_id,
            "title": policy.title,
            "content": content,
        }, ensure_ascii=False, indent=2)
