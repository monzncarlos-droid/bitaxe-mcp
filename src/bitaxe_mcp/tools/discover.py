"""LAN discovery tool."""

from __future__ import annotations

from bitaxe_mcp import client
from bitaxe_mcp import discovery
from bitaxe_mcp.server import mcp


@mcp.tool()
async def bitaxe_discover(subnet: str | None = None) -> str:
    """
    Scan the local network for active BitAXE devices and return their addresses.

    Args:
        subnet: an optional IPv4 CIDR to scan (e.g. "192.168.1.0/24").
            When omitted, the host's own local subnet is auto-detected and used.

    Probes every host on the subnet concurrently for the BitAXE info endpoint
    (short timeouts, bounded concurrency) and reports the ones that respond.
    Returns ``{ "subnet": "<cidr>", "count": N, "devices": [
    {"ip": "...", "asicModel": "...", "hostname": "..."}, ... ] }`` as a
    pretty-printed JSON string with ``count`` equal to ``len(devices)``.
    """
    network = discovery.parse_subnet(subnet)
    devices = await discovery.run_discovery(network)
    payload = {"subnet": str(network), "count": len(devices), "devices": devices}
    return client._format_json(payload)
