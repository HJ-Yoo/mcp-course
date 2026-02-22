"""TODO (Episode 7-8): Implement policy search tool."""
from __future__ import annotations

def register(mcp):
    @mcp.tool()
    async def search_policy(query: str, ctx) -> str:
        """Search internal policies by keyword."""
        # TODO: Get AppContext from ctx
        # TODO: Search policy markdown files
        # TODO: Return matches with snippets
        # TODO: Add audit logging (Episode 14)
        return "Not implemented yet"
