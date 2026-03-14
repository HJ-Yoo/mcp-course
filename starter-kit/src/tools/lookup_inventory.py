"""TODO (Episode 5-6): Implement inventory lookup tool."""
from __future__ import annotations

def register(mcp):
    @mcp.tool()
    async def lookup_inventory(query: str, ctx) -> str:
        """Search IT inventory by keyword. Returns matching equipment items."""
        # TODO: Get AppContext from ctx
        # TODO: Sanitize query
        # TODO: Build SQL LIKE query and execute on app.db
        # TODO: Convert rows to JSON with [dict(row) for row in rows]
        # TODO: Add audit logging (Episode 14)
        return "Not implemented yet"
