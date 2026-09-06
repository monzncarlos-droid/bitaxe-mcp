"""Read-only monitoring tools (GET endpoints)."""

from __future__ import annotations

from bitaxe_mcp import client
from bitaxe_mcp.server import mcp


@mcp.tool()
async def bitaxe_status(miner: str) -> str:
    """
    Get full system info for a specific BitAXE gamma miner *miner*.
    Args:
        miner: the name of the miner to query for status
    Returns the complete JSON response from ``GET /api/system/info``
    formatted as a pretty-printed string.
    """
    resp = await client._http_request("get", miner, "/api/system/info")
    resp.raise_for_status()
    return client._format_json(resp.json())


@mcp.tool()
async def bitaxe_stats(miner: str, columns: list[str] | None = None) -> str:
    """
    Get statistics for a specific *miner*, optionally filtered by *columns*.
    Args:
        miner: the name of the miner to query for statistics
        columns: a list of names to filter the results by
    Example columns: ``["hashrate", "asicTemp", "power"]``
    """
    params = None
    if columns:
        params = {"columns": ",".join(columns)}
    resp = await client._http_request("get", miner, "/api/system/statistics", params=params)
    resp.raise_for_status()
    return client._format_json(resp.json())


@mcp.tool()
async def bitaxe_asic_info(miner: str) -> str:
    """Get BitAXE gamme ASIC capabilities (model, default frequency, frequency/voltage options).
       Args:
           miner: the name of the miner to query for asic info 
    """
    resp = await client._http_request("get", miner, "/api/system/asic")
    resp.raise_for_status()
    return client._format_json(resp.json())


@mcp.tool()
async def bitaxe_scan_wifi(miner: str) -> str:
    """
    Scan for available WiFi networks in the vacinity of *miner*.
    Args:
        miner: the name of the miner to query for wifi scan info
    """
    resp = await client._http_request("get", miner, "/api/system/wifi/scan")
    resp.raise_for_status()
    return client._format_json(resp.json())
