"""Test fixtures: MINERS_CONFIG, httpx.MockTransport handler, sample responses."""
from __future__ import annotations

import json

import httpx
import pytest


# ----------------------------------------------------------------
# Sample mock response bodies for each endpoint
# ----------------------------------------------------------------

SAMPLE_SYSTEM_INFO = {
    "minerId": "test-1234",
    "model": "gamma",
    "firmware": "1.0.0",
    "ipAddress": "192.168.1.100",
    "hashRate": 110_000,
    "fanSpeed": 50,
    "asicTemp": 72,
    "power": 1100,
}

SAMPLE_STATS = {
    "hashrate": 110_000,
    "difficulty": 8_500_000_000_000,
    "accepted": 342,
    "rejected": 1,
    "hardwareErrors": 0,
    "utility": {"total": 341, "lastMinute": 3},
}

SAMPLE_ASIC_INFO = {
    "model": "BM1366",
    "defaultFrequency": 550,
    "frequencyOptions": [500, 550, 600, 650],
    "voltageOptions": [750, 850, 950],
}

SAMPLE_WIFI_SCAN = [
    {"ssid": "HomeNetwork", "rssi": -45, "channel": 6},
    {"ssid": "Office5G", "rssi": -72, "channel": 36},
]


def make_response_handler(code: int = 200):
    """Return a MockTransport handler that responds with *code*-appropriate data."""

    def handler(request):
        path = request.url.path
        method = request.method.upper()

        if path == "/api/system/info":
            body_text = json.dumps(SAMPLE_SYSTEM_INFO)
        elif path == "/api/system/statistics":
            body_text = json.dumps(SAMPLE_STATS)
        elif path == "/api/system/asic":
            body_text = json.dumps(SAMPLE_ASIC_INFO)
        elif path == "/api/system/wifi/scan":
            body_text = json.dumps(SAMPLE_WIFI_SCAN)
        elif path == "/api/system/restart":
            body_text = json.dumps({"action": "restart", "status": "ok"})
        elif path == "/api/system/identify":
            body_text = json.dumps({"action": "identify", "status": "ok"})
        elif path == "/api/system":
            if method == "PATCH":
                # For PATCH we accept the request but won't inspect body here in the handler;
                # that is tested via recorded requests instead.
                body_text = json.dumps({"applied": True, "status": "updated"})
            else:
                return httpx.Response(405, json={"error": "method not allowed"})
        elif code == 404 or path.startswith("/nonexistent"):
            return httpx.Response(code, json={"error": "not found"})
        elif path in ("/api/system",):
            # For GET on /api/system (incorrect method) return 404
            return httpx.Response(404, json={"error": "method not allowed"})
        else:
            return httpx.Response(code, json={"error": "not found"})

        headers = {"content-type": "application/json"}
        return httpx.Response(200 if code == 200 else code, text=body_text or "{}", headers=headers)

    return handler


# ----------------------------------------------------------------
# Global: ensure MINERS_CONFIG is set (overridable per-test)
# ----------------------------------------------------------------

@pytest.fixture(autouse=True)
def _inject_miners_config(monkeypatch):
    """Default MINERS_CONFIG for all tests."""
    default = json.dumps({"miners": {"test-miner": {"ip": "192.168.1.100"}}})
    monkeypatch.setenv("MINERS_CONFIG", default)
    from bitaxe_mcp import config as cfg
    cfg.load_config()


def _make_patched_request(transport: httpx.MockTransport):
    """Return an async stand-in for ``bitaxe_mcp.client._http_request`` using *transport*."""
    from bitaxe_mcp import config as cfg

    async def patched(method, miner, path, **kwargs):
        ip = cfg.get_miner_ip(miner)
        url = f"http://{ip}{path}"
        # Use MockTransport directly as the transport; this captures all HTTP calls.
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await getattr(client, method)(url, **kwargs)
        return resp

    return patched


# ----------------------------------------------------------------
# Fixture: patch bitaxe_mcp.client._http_request to use httpx.MockTransport
# ----------------------------------------------------------------

@pytest.fixture
def mock_transport(monkeypatch):
    """Patch bitaxe_mcp.client._http_request so every HTTP call goes through MockTransport with 200s."""
    from bitaxe_mcp import client

    transport = httpx.MockTransport(make_response_handler())
    monkeypatch.setattr(client, "_http_request", _make_patched_request(transport))
    return transport


@pytest.fixture
def error_500_transport(monkeypatch):
    """Patch bitaxe_mcp.client._http_request so it returns HTTP 500."""
    from bitaxe_mcp import client

    transport = httpx.MockTransport(make_response_handler(500))
    monkeypatch.setattr(client, "_http_request", _make_patched_request(transport))
    return transport


@pytest.fixture
def error_404_transport(monkeypatch):
    """Patch bitaxe_mcp.client._http_request so it returns HTTP 404."""
    from bitaxe_mcp import client

    handler404 = make_response_handler(404)
    transport = httpx.MockTransport(handler404)
    monkeypatch.setattr(client, "_http_request", _make_patched_request(transport))
    return transport


@pytest.fixture
def test_miner_ip():
    """Return the configured IP of the default test miner."""
    return "192.168.1.100"
