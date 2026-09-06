"""Shared HTTP client for the BitAXE miner API."""

from __future__ import annotations

import json

import httpx

from bitaxe_mcp import config as cfg

HTTP_TIMEOUT_CONNECT = 5.0
HTTP_TIMEOUT_READ = 10.0


def _format_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


async def _http_request(method: str, miner: str, path: str, **kwargs) -> httpx.Response:
    ip = cfg.get_miner_ip(miner)
    url = f"http://{ip}{path}"
    client = httpx.AsyncClient(timeout=httpx.Timeout(HTTP_TIMEOUT_CONNECT, read=HTTP_TIMEOUT_READ))
    async with client as c:
        resp = await getattr(c, method)(url, **kwargs)
    return resp
