"""TODO (Episode 9-10): Implement ticket creation tool."""
from __future__ import annotations

def register(mcp):
    @mcp.tool()
    async def create_ticket(title: str, body: str, priority: str, confirm: bool = False, idempotency_key: str | None = None, ctx=None) -> str:
        """Create an IT support ticket with confirmation gate."""
        # TODO: Validate inputs
        # TODO: Preview mode (confirm=False)
        # TODO: Idempotency check
        # TODO: Create ticket
        # TODO: Add audit logging (Episode 14)
        return "Not implemented yet"
