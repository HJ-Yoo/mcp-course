"""
Internal Ops Assistant — MCP Server (Starter Kit)

TODO (Episode 4): Wire together tools, resources, and prompts.
"""
from __future__ import annotations
import argparse
from mcp.server.fastmcp import FastMCP

# TODO (Episode 3): Import AppContext and create lifespan
# TODO (Episode 3): Initialize FastMCP with lifespan

mcp = FastMCP("internal-ops-assistant")

# TODO (Episode 5): Register lookup_inventory tool
# TODO (Episode 7): Register search_policy tool
# TODO (Episode 9): Register create_ticket tool
# TODO (Episode 11): Register policy resources
# TODO (Episode 13): Register prompt templates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # TODO (Episode 4): Add transport selection logic
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
