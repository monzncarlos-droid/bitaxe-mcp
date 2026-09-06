"""Stratum pool configuration tool (PATCH /api/system)."""

from __future__ import annotations

from bitaxe_mcp import client
from bitaxe_mcp.server import mcp


@mcp.tool()
async def bitaxe_set_pool(
    miner: str,
    url: str,
    port: int | None = None,
    user: str | None = None,
    pass_: str = "x",
    fallback_url: str | None = None,
    fallback_port: int | None = None,
    fallback_user: str | None = None,
) -> str:
    """Configure the primary and/or fallback stratum pool on *miner*.
    Args:
        miner: the name of the miner whose pool config will be updated
        url: The pool's url
        port: The pool's port number
        user: The user name for the pool (optional)
        pass_: The user password for the pool (optional)
        fallback_url: The fallback pool's url
        fallback_port: The fallback pool's port number
        fallback_user: The user name for the fallback pool (optional)

    *url* is required.  Optional fields allow a partial pool update.
    """
    body: dict = {"url": url, "pass": pass_}
    if port is not None:
        body["port"] = port
    if user is not None:
        body["user"] = user
    if fallback_url is not None:
        body["fallbackurl"] = fallback_url
    if fallback_port is not None:
        body["fallbackport"] = fallback_port
    if fallback_user is not None:
        body["fallbackuser"] = fallback_user
    resp = await client._http_request("patch", miner, "/api/system", json=body)
    resp.raise_for_status()
    return client._format_json({"applied": body, "response": resp.json()})
