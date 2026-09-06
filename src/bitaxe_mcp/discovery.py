"""LAN discovery helpers for finding online BitAXE devices."""

from __future__ import annotations

import asyncio
import ipaddress
import socket

import httpx

DISCOVERY_CONNECT_TIMEOUT = 0.5
DISCOVERY_READ_TIMEOUT = 1.0
DISCOVERY_CONCURRENCY = 8


def detect_local_subnet() -> ipaddress.IPv4Network:
    """Return the host's local subnet as an ``IPv4Network``.

    Uses a UDP socket bound toward a public endpoint to discover the local
    IP, then derives the /24 subnet. Falls back to 127.0.0.1/8 if the trick
    fails (no routing / no network).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except OSError:
        local_ip = "127.0.0.1"
    return ipaddress.IPv4Network(f"{local_ip}/24", strict=False)


def _candidate_hosts(network: ipaddress.IPv4Network) -> list[str]:
    """Expand *network* into candidate host IPs.

    For a /31 or /32 the broadcast address is not distinct, so use the
    network address itself (or the single host) as the only candidate.
    """
    if network.prefixlen >= 31:
        return [str(network.network_address)]
    hosts = list(network.hosts())
    return [str(h) for h in hosts]


def parse_subnet(subnet: str | None) -> ipaddress.IPv4Network:
    """Resolve a *subnet* argument to an ``IPv4Network``.

    When *subnet* is omitted, default to the host's local subnet. Raises
    ``ValueError`` if the supplied value is not a valid IPv4 CIDR network.
    """
    if subnet is None:
        return detect_local_subnet()
    try:
        net = ipaddress.ip_network(subnet, strict=False)
    except ValueError as exc:
        raise ValueError(f"Invalid subnet (must be IPv4 CIDR, e.g. 192.168.1.0/24): {subnet!r}") from exc
    if not isinstance(net, ipaddress.IPv4Network):
        raise ValueError(f"Invalid subnet (must be IPv4): {subnet!r}")
    return net


async def probe_host(ip: str) -> dict | None:
    """GET ``http://{ip}/api/system/info`` and return miner info, or ``None``.

    Returns ``None`` on any error, timeout, non-2xx response, or a body that
    does not look like a BitAXE (no ``ASICModel`` field).
    """
    url = f"http://{ip}/api/system/info"
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(DISCOVERY_CONNECT_TIMEOUT, read=DISCOVERY_READ_TIMEOUT)
        ) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if "ASICModel" not in data:
            return None
        return {
            "ip": ip,
            "asicModel": data.get("ASICModel"),
            "hostname": data.get("hostname"),
        }
    except Exception:
        return None


async def run_discovery(network: ipaddress.IPv4Network) -> list[dict]:
    """Probe every candidate host in *network* concurrently.

    Returns only successful probes, sorted by IP for stable output. Per-host
    failures are ignored. Concurrency is bounded to avoid saturating the NIC.
    """
    hosts = _candidate_hosts(network)
    sem = asyncio.Semaphore(DISCOVERY_CONCURRENCY)

    async def guarded(ip: str) -> dict | None:
        async with sem:
            return await probe_host(ip)

    results = await asyncio.gather(*(guarded(ip) for ip in hosts))
    devices = [r for r in results if r is not None]
    devices.sort(key=lambda d: ipaddress.ip_address(d["ip"]))
    return devices
