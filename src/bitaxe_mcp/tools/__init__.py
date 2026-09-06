"""MCP tool functions for bitaxe-mcp, grouped by domain.

Importing any of the submodules registers their tools on the shared FastMCP
instance (``bitaxe_mcp.server.mcp``). Import from ``bitaxe_mcp.tools`` (or import
``bitaxe_mcp.server``) to have all tools registered.
"""

from bitaxe_mcp.tools import configure, discover, maintenance, monitor, pool  # noqa: F401

__all__ = ["configure", "discover", "maintenance", "monitor", "pool"]
