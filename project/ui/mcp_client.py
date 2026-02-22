"""
MCP Client wrapper — connects to the Internal Ops Assistant server
via stdio or Streamable HTTP, discovers tools/resources, and executes calls.

Usage:
    client = MCPClient(transport="stdio")
    await client.connect()
    tools = await client.list_tools()
    result = await client.call_tool("lookup_inventory", {"query": "laptop"})
    await client.disconnect()
"""

from __future__ import annotations

import asyncio
import json
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


@dataclass
class ToolCallLog:
    """A single MCP tool call record for display in the UI."""
    tool_name: str
    arguments: dict[str, Any]
    result: str
    success: bool
    duration_ms: float = 0.0


@dataclass
class MCPClient:
    """Thin wrapper around MCP ClientSession supporting both transports."""

    transport: str = "stdio"
    server_command: str = "uv"
    server_args: list[str] = field(default_factory=lambda: [
        "run", "python", "src/server.py", "--transport", "stdio",
    ])
    server_cwd: str | None = None
    http_url: str = "http://localhost:8000/mcp"

    # Internal state
    _session: ClientSession | None = field(default=None, repr=False)
    _exit_stack: AsyncExitStack | None = field(default=None, repr=False)
    _tools_cache: list[dict] | None = field(default=None, repr=False)
    _resources_cache: list[dict] | None = field(default=None, repr=False)
    _logs: list[ToolCallLog] = field(default_factory=list, repr=False)

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    @property
    def logs(self) -> list[ToolCallLog]:
        return list(self._logs)

    def clear_logs(self) -> None:
        self._logs.clear()

    # ------------------------------------------------------------------
    # Connect / Disconnect
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._session is not None:
            return

        self._exit_stack = AsyncExitStack()

        if self.transport == "stdio":
            cwd = self.server_cwd or str(
                Path(__file__).resolve().parent.parent
            )
            server_params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                cwd=cwd,
            )
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
        elif self.transport == "streamable-http":
            read_stream, write_stream, _ = await self._exit_stack.enter_async_context(
                streamablehttp_client(self.http_url)
            )
        else:
            raise ValueError(f"Unknown transport: {self.transport}")

        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

        # Pre-cache tool and resource lists
        self._tools_cache = None
        self._resources_cache = None

    async def disconnect(self) -> None:
        """Close the MCP session and underlying transport."""
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
        self._session = None
        self._exit_stack = None
        self._tools_cache = None
        self._resources_cache = None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    async def list_tools(self) -> list[dict]:
        """Return the list of tools exposed by the server."""
        assert self._session, "Not connected. Call connect() first."
        if self._tools_cache is None:
            result = await self._session.list_tools()
            self._tools_cache = [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": t.inputSchema if hasattr(t, "inputSchema") else {},
                }
                for t in result.tools
            ]
        return self._tools_cache

    async def list_resources(self) -> list[dict]:
        """Return the list of resources exposed by the server."""
        assert self._session, "Not connected. Call connect() first."
        if self._resources_cache is None:
            result = await self._session.list_resources()
            self._resources_cache = [
                {
                    "uri": str(r.uri),
                    "name": r.name or "",
                    "description": r.description or "",
                }
                for r in result.resources
            ]
        return self._resources_cache

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool and return the text result."""
        assert self._session, "Not connected. Call connect() first."

        import time
        t0 = time.perf_counter()
        success = True

        try:
            result = await self._session.call_tool(name, arguments)
            # Extract text content
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
                else:
                    parts.append(str(content))
            text = "\n".join(parts)
            if result.isError:
                success = False
        except Exception as e:
            text = f"Error: {e}"
            success = False

        duration_ms = (time.perf_counter() - t0) * 1000

        self._logs.append(ToolCallLog(
            tool_name=name,
            arguments=arguments,
            result=text[:500],
            success=success,
            duration_ms=round(duration_ms, 1),
        ))

        return text

    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI."""
        assert self._session, "Not connected. Call connect() first."
        result = await self._session.read_resource(uri)
        parts = []
        for content in result.contents:
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Claude-compatible tool definitions
    # ------------------------------------------------------------------
    async def get_claude_tools(self) -> list[dict]:
        """Convert MCP tools to Anthropic Claude tool_use format."""
        mcp_tools = await self.list_tools()
        claude_tools = []
        for t in mcp_tools:
            claude_tools.append({
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            })
        return claude_tools
