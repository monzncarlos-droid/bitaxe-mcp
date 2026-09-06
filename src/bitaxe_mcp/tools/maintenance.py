"""Maintenance and server-level config tools."""

from __future__ import annotations

from bitaxe_mcp import client
from bitaxe_mcp import config as cfg
from bitaxe_mcp.server import mcp


@mcp.tool()
async def bitaxe_restart(miner: str) -> str:
    """
    Request *miner* to reboot
    Args:
        miner: the name of the miner to restart
    """
    resp = await client._http_request("post", miner, "/api/system/restart")
    resp.raise_for_status()
    return client._format_json({"action": "restart", "response": resp.json()})


@mcp.tool()
async def bitaxe_identify(miner: str) -> str:
    """
    "Identify" *miner* — front-panel LED blinks / beep.
    Args:
        miner: the name of the miner to identify
    """
    resp = await client._http_request("post", miner, "/api/system/identify")
    resp.raise_for_status()
    return client._format_json({"action": "identify", "response": resp.json()})


@mcp.tool()
async def bitaxe_list_miners() -> str:
    """
    Return the full miners configuration as a JSON dict so the LLM can see
    how many miners are configured and their names/addresses.

    No *miner* parameter is needed — this returns server-level config.
    Returns ``{ "miners": { "<name>": { "ip": "..." }, ... }, "count": N }``.
    """
    miners_cfg = cfg.get_miner_config()
    payload = {"miners": miners_cfg, "count": len(miners_cfg)}
    return client._format_json(payload)
