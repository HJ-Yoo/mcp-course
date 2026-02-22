"""
Internal Ops Assistant — MCP Server (Reference Implementation)

This is the main entry point. It wires together all tools, resources,
and prompts into a single FastMCP server and supports both stdio and
Streamable HTTP transports.
"""

from __future__ import annotations

import argparse
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from src.models import AppContext


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Load shared state once at startup and inject via context."""
    ctx = AppContext.load()
    yield {"app": ctx}


mcp = FastMCP(
    "internal-ops-assistant",
    lifespan=app_lifespan,
)

# ------------------------------------------------------------------
# Register components (imported for side-effects)
# ------------------------------------------------------------------
from src.tools.lookup_inventory import register as _reg_inv      # noqa: E402, F401
from src.tools.search_policy import register as _reg_search       # noqa: E402, F401
from src.tools.create_ticket import register as _reg_ticket       # noqa: E402, F401
from src.resources.policy import register as _reg_policy          # noqa: E402, F401
from src.prompts.templates import register as _reg_prompts        # noqa: E402, F401

_reg_inv(mcp)
_reg_search(mcp)
_reg_ticket(mcp)
_reg_policy(mcp)
_reg_prompts(mcp)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Internal Ops Assistant MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
        )


if __name__ == "__main__":
    main()
