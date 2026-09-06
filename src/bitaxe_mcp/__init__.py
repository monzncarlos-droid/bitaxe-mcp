"""BitAXE MCP — monitoring and configuration tools for BitAXE Bitcoin ASIC miners.

The ``bitaxe_mcp`` package provides an installable MCP server (stdio transport)
plus the building blocks it is composed of:

- ``bitaxe_mcp.config``    — MINERS_CONFIG parsing, validation and IP resolution
- ``bitaxe_mcp.client``    — shared HTTP request helper for the miner API
- ``bitaxe_mcp.discovery`` — LAN subnet detection and concurrent host probing
- ``bitaxe_mcp.tools``     — the MCP tool functions, grouped by domain
- ``bitaxe_mcp.server``    — the FastMCP instance and the ``main()`` entry point
"""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("bitaxe-mcp")
except PackageNotFoundError:  # running from a source checkout without installing
    __version__ = "0.0.0"
