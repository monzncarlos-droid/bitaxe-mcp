"""FastMCP server instance and entry point for bitaxe-mcp.

Run as stdio transport::

    bitaxe-mcp
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from bitaxe_mcp import config as cfg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bitaxe-mcp")


# ------------------------------------------------------------------
# Lifespan: validate config on startup
# ------------------------------------------------------------------

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Load and validate MINERS_CONFIG."""
    logger.info("Loading MINERS_CONFIG…")
    miners = cfg.load_config()
    names = ", ".join(miners.keys())
    # Store on server instance for later use
    server.context = {"miners": miners}
    logger.info("Loaded miners: %s", names)
    yield


mcp = FastMCP(
    "bitaxe-mcp",
    instructions="Monitor and configure Bitcoin ASIC miners (BitAXE).",
    lifespan=server_lifespan,
)

# Side-effect imports: import the tool modules so their @mcp.tool()
# decorators register on the shared `mcp` instance.
from bitaxe_mcp.tools import configure, discover, maintenance, monitor, pool  # noqa: E402,F401


# ------------------------------------------------------------------
# __main__
# ------------------------------------------------------------------

def main() -> None:
    """Console-script entry point: start the stdio MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
