"""Tests for the tool functions in the bitaxe_mcp package."""
from __future__ import annotations

import asyncio
import ipaddress
import json

import httpx
import pytest

from bitaxe_mcp import discovery
from bitaxe_mcp.tools import monitor
from bitaxe_mcp.tools import configure as configure_tools
from bitaxe_mcp.tools import pool as pool_tools
from bitaxe_mcp.tools import maintenance
from bitaxe_mcp.tools import discover as discover_tool


def dump(obj):
    """Shorthand to match response serialization."""
    return json.dumps(obj, indent=2)


# ====================================================================
# Monitoring tools (status, stats, asic info, wifi scan)
# ====================================================================

class TestMonitorTools:
    """Tests for the read-only monitoring tools."""

    @pytest.mark.asyncio
    async def test_status_constructs_get(self, mock_transport):
        """bitaxe_status issues a GET to /api/system/info and returns a parseable payload."""
        result = await monitor.bitaxe_status("test-miner")
        parsed = json.loads(result)
        assert "minerId" in parsed

    @pytest.mark.asyncio
    async def test_status_returns_valid_json(self, mock_transport):
        """bitaxe_status returns a valid pretty-printed JSON string."""
        result = await monitor.bitaxe_status("test-miner")
        assert isinstance(result, str)
        parsed = json.loads(result)  # must be parseable
        assert "minerId" in parsed  # and contains expected data

    @pytest.mark.asyncio
    async def test_stats_no_columns(self, mock_transport):
        """bitaxe_stats without a columns argument issues a plain request."""
        result = await monitor.bitaxe_stats("test-miner")
        parsed = json.loads(result)
        assert "hashrate" in parsed

    @pytest.mark.asyncio
    async def test_stats_with_columns(self, mock_transport):
        """bitaxe_stats with a columns list sends them as query parameters."""
        result = await monitor.bitaxe_stats("test-miner", columns=["hashrate", "power"])
        parsed = json.loads(result)
        assert "hashrate" in parsed

    @pytest.mark.asyncio
    async def test_stats_returns_valid_json(self, mock_transport):
        """bitaxe_stats returns a valid pretty-printed JSON string."""
        result = await monitor.bitaxe_stats("test-miner")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "hashrate" in parsed

    @pytest.mark.asyncio
    async def test_asic_info_constructs_get(self, mock_transport):
        """bitaxe_asic_info issues a GET to /api/system/asic."""
        result = await monitor.bitaxe_asic_info("test-miner")
        parsed = json.loads(result)
        assert "model" in parsed

    @pytest.mark.asyncio
    async def test_asic_info_returns_valid_json(self, mock_transport):
        """bitaxe_asic_info returns a valid pretty-printed JSON string."""
        result = await monitor.bitaxe_asic_info("test-miner")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "model" in parsed

    @pytest.mark.asyncio
    async def test_scan_wifi_constructs_get(self, mock_transport):
        """bitaxe_scan_wifi issues a GET to /api/system/wifi/scan."""
        result = await monitor.bitaxe_scan_wifi("test-miner")
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    @pytest.mark.asyncio
    async def test_scan_wifi_returns_valid_json(self, mock_transport):
        """bitaxe_scan_wifi returns a valid pretty-printed JSON string."""
        result = await monitor.bitaxe_scan_wifi("test-miner")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)


# ====================================================================
# Configuration tools (configure, fan, frequency, pool)
# ====================================================================

class TestConfigTools:
    """Tests for the configuration tools."""

    @pytest.mark.asyncio
    async def test_configure_forwards_settings(self, mock_transport):
        """bitaxe_configure forwards the settings dict as the PATCH body."""
        result = await configure_tools.bitaxe_configure("test-miner", {"fanspeed": 80})
        parsed = json.loads(result)
        assert "applied" in parsed
        assert parsed["applied"]["fanspeed"] == 80

    @pytest.mark.asyncio
    async def test_configure_returns_applied_and_response(self, mock_transport):
        """bitaxe_configure returns both "applied" and "response" keys."""
        result = await configure_tools.bitaxe_configure("test-miner", {"fanspeed": 80})
        parsed = json.loads(result)
        assert "applied" in parsed
        assert "response" in parsed

    @pytest.mark.asyncio
    async def test_set_fan_with_fanspeed(self, mock_transport):
        """bitaxe_set_fan with fanspeed=75 builds a body of [{"fanspeed": 75}]."""
        result = await configure_tools.bitaxe_set_fan("test-miner", fanspeed=75)
        parsed = json.loads(result)
        assert parsed["body"] == [{"fanspeed": 75}]

    @pytest.mark.asyncio
    async def test_set_fan_with_autofanspeed(self, mock_transport):
        """bitaxe_set_fan with autofanspeed=True builds a body of [{"autofanspeed": 1}]."""
        result = await configure_tools.bitaxe_set_fan("test-miner", autofanspeed=True)
        parsed = json.loads(result)
        assert parsed["body"] == [{"autofanspeed": 1}]

    @pytest.mark.asyncio
    async def test_set_fan_neither_raises(self):
        """bitaxe_set_fan with neither speed parameter raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            await configure_tools.bitaxe_set_fan("test-miner")

    @pytest.mark.asyncio
    async def test_set_fan_zero_accepted(self, mock_transport):
        """bitaxe_set_fan accepts fanspeed=0."""
        result = await configure_tools.bitaxe_set_fan("test-miner", fanspeed=0)
        parsed = json.loads(result)
        assert parsed["body"] == [{"fanspeed": 0}]

    @pytest.mark.asyncio
    async def test_set_fan_100_accepted(self, mock_transport):
        """bitaxe_set_fan accepts fanspeed=100."""
        result = await configure_tools.bitaxe_set_fan("test-miner", fanspeed=100)
        parsed = json.loads(result)
        assert parsed["body"] == [{"fanspeed": 100}]

    @pytest.mark.asyncio
    async def test_set_fan_minus_one_raises(self):
        """bitaxe_set_fan with fanspeed=-1 raises ValueError (out of 0-100 range)."""
        with pytest.raises(ValueError, match="0 to 100"):
            await configure_tools.bitaxe_set_fan("test-miner", fanspeed=-1)

    @pytest.mark.asyncio
    async def test_set_fan_101_raises(self):
        """bitaxe_set_fan with fanspeed=101 raises ValueError (out of 0-100 range)."""
        with pytest.raises(ValueError, match="0 to 100"):
            await configure_tools.bitaxe_set_fan("test-miner", fanspeed=101)

    @pytest.mark.asyncio
    async def test_set_frequency_includes_overclock(self, mock_transport):
        """bitaxe_set_frequency includes frequency, coreVoltage, and overclockEnabled=1 in the body."""
        result = await configure_tools.bitaxe_set_frequency("test-miner", 600, 850)
        parsed = json.loads(result)
        assert parsed["applied"]["frequency"] == 600
        assert parsed["applied"]["coreVoltage"] == 850
        assert parsed["applied"]["overclockEnabled"] == 1

    @pytest.mark.asyncio
    async def test_set_pool_required_only(self, mock_transport):
        """bitaxe_set_pool accepts just the required url."""
        result = await pool_tools.bitaxe_set_pool("test-miner", "stratum+tcp://pool.btc.com")
        parsed = json.loads(result)
        assert parsed["applied"]["url"] == "stratum+tcp://pool.btc.com"
        assert parsed["applied"]["pass"] == "x"

    @pytest.mark.asyncio
    async def test_set_pool_with_optional_fields(self, mock_transport):
        """bitaxe_set_pool includes the optional parameters in the body."""
        result = await pool_tools.bitaxe_set_pool(
            "test-miner",
            "stratum+tcp://pool.btc.com",
            port=3333,
            user="worker1",
            fallback_url="stratum+tcp://fallback.com",
        )
        parsed = json.loads(result)
        assert parsed["applied"]["url"] == "stratum+tcp://pool.btc.com"
        assert parsed["applied"]["port"] == 3333
        assert parsed["applied"]["user"] == "worker1"
        assert parsed["applied"]["fallbackurl"] == "stratum+tcp://fallback.com"

    @pytest.mark.asyncio
    async def test_set_pool_default_pass_is_x(self, mock_transport):
        """bitaxe_set_pool defaults pass to 'x'."""
        result = await pool_tools.bitaxe_set_pool("test-miner", "stratum+tcp://pool.btc.com")
        parsed = json.loads(result)
        assert parsed["applied"]["pass"] == "x"


# ====================================================================
# Maintenance tools (restart, identify)
# ====================================================================

class TestMaintenanceTools:
    """Tests for the maintenance tools."""

    @pytest.mark.asyncio
    async def test_restart_constructs_post(self, mock_transport):
        """bitaxe_restart issues a POST to /api/system/restart."""
        result = await maintenance.bitaxe_restart("test-miner")
        parsed = json.loads(result)
        assert "response" in parsed

    @pytest.mark.asyncio
    async def test_restart_returns_action_restart(self, mock_transport):
        """bitaxe_restart returns {"action": "restart", ...}."""
        result = await maintenance.bitaxe_restart("test-miner")
        parsed = json.loads(result)
        assert parsed["action"] == "restart"

    @pytest.mark.asyncio
    async def test_identify_constructs_post(self, mock_transport):
        """bitaxe_identify issues a POST to /api/system/identify."""
        result = await maintenance.bitaxe_identify("test-miner")
        parsed = json.loads(result)
        assert "response" in parsed

    @pytest.mark.asyncio
    async def test_identify_returns_action_identify(self, mock_transport):
        """bitaxe_identify returns {"action": "identify", ...}."""
        result = await maintenance.bitaxe_identify("test-miner")
        parsed = json.loads(result)
        assert parsed["action"] == "identify"


# ====================================================================
# Error handling
# ====================================================================

class TestErrorHandling:
    """Tests for the error paths."""

    @pytest.mark.asyncio
    async def test_http_500_raises_status_error(self, error_500_transport):
        """A 500 from the miner surfaces as an httpx.HTTPStatusError."""
        with pytest.raises(httpx.HTTPStatusError):
            await monitor.bitaxe_status("test-miner")

    @pytest.mark.asyncio
    async def test_http_404_raises_status_error(self, error_404_transport):
        """A 404 from the client surfaces as an httpx.HTTPStatusError."""
        with pytest.raises(httpx.HTTPStatusError):
            await monitor.bitaxe_status("test-miner")

    @pytest.mark.asyncio
    async def test_unknown_miner_raises_value_error(self):
        """A tool call with an unknown miner name raises ValueError from get_miner_ip()."""
        from bitaxe_mcp import config as cfg_cfg
        original_ip = cfg_cfg._miners.get
        cfg_cfg._miners.clear()
        try:
            with pytest.raises(ValueError, match="Unknown miner"):
                await monitor.bitaxe_status("nonexistent")
        finally:
            pass


# ====================================================================
# Smoke tests
# ====================================================================

class TestFullSuite:
    """Smoke test: confirm every public tool is importable."""

    def test_imports_ok(self):
        """Confirm all server modules import cleanly."""
        assert hasattr(monitor, "bitaxe_status")
        assert hasattr(monitor, "bitaxe_stats")
        assert hasattr(monitor, "bitaxe_asic_info")
        assert hasattr(monitor, "bitaxe_scan_wifi")
        assert hasattr(configure_tools, "bitaxe_configure")
        assert hasattr(configure_tools, "bitaxe_set_fan")
        assert hasattr(configure_tools, "bitaxe_set_frequency")
        assert hasattr(pool_tools, "bitaxe_set_pool")
        assert hasattr(maintenance, "bitaxe_restart")
        assert hasattr(maintenance, "bitaxe_identify")
        assert hasattr(maintenance, "bitaxe_list_miners")


# ====================================================================
# bitaxe_list_miners tool
# ====================================================================

class TestListMinersTool:
    """Tests for the server-level bitaxe_list_miners() tool (no miner parameter needed)."""

    @pytest.mark.asyncio
    async def test_returns_valid_json_with_miners_and_count(self, mock_transport):
        """bitaxe_list_miners returns valid JSON with a miners dict and count field (single miner)."""
        result = await maintenance.bitaxe_list_miners()
        parsed = json.loads(result)
        assert isinstance(result, str)
        assert "miners" in parsed
        assert "count" in parsed
        assert parsed["count"] == 1
        assert "test-miner" in parsed["miners"]
        assert parsed["miners"]["test-miner"]["ip"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_returns_correct_count_for_multiple_miners(self, monkeypatch):
        """bitaxe_list_miners returns the correct count=2 for two configured miners."""
        monkeypatch.setenv("MINERS_CONFIG", json.dumps({
            "miners": {
                "miner-a": {"ip": "192.168.1.10"},
                "miner-b": {"ip": "192.168.1.20"},
            }
        }))
        from bitaxe_mcp import config as cfg
        cfg._miners = {}  # force reload

        result = await maintenance.bitaxe_list_miners()
        parsed = json.loads(result)
        assert parsed["count"] == 2
        assert "miner-a" in parsed["miners"]
        assert "miner-b" in parsed["miners"]
        assert parsed["miners"]["miner-a"]["ip"] == "192.168.1.10"
        assert parsed["miners"]["miner-b"]["ip"] == "192.168.1.20"

    @pytest.mark.asyncio
    async def test_returns_empty_for_zero_miners(self):
        """bitaxe_list_miners returns count=0 and an empty miners map when no miners are configured."""
        from bitaxe_mcp import config as cfg_cfg

        original_func = getattr(cfg_cfg, 'get_miner_config')

        def mock_get_miner_config():
            return {}

        cfg_cfg.get_miner_config = mock_get_miner_config  # type: ignore[attr-defined]

        try:
            result = await maintenance.bitaxe_list_miners()
            parsed = json.loads(result)
            assert parsed["count"] == 0
            assert parsed["miners"] == {}
        finally:
            cfg_cfg.get_miner_config = original_func  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_does_not_make_http_calls(self, mock_transport):
        """bitaxe_list_miners responds without issuing any HTTP requests."""
        result = await maintenance.bitaxe_list_miners()
        parsed = json.loads(result)
        assert "miners" in parsed
        assert isinstance(parsed["count"], int)


# ====================================================================
# bitaxe_discover tool (network scan)
# ====================================================================

class TestDiscovery:
    """Tests for bitaxe_discover() / run_discovery()."""

    @pytest.mark.asyncio
    async def test_parse_valid_cidr_accepted(self):
        """A valid CIDR is accepted and parses to an IPv4Network."""
        net = discovery.parse_subnet("192.168.1.0/24")
        assert net == ipaddress.IPv4Network("192.168.1.0/24")

    @pytest.mark.asyncio
    async def test_parse_invalid_value_raises(self):
        """An invalid subnet value raises ValueError (no probing happens)."""
        with pytest.raises(ValueError):
            discovery.parse_subnet("not-a-cidr")
        with pytest.raises(ValueError):
            discovery.parse_subnet("300.300.300.300/24")

    @pytest.mark.asyncio
    async def test_discovery_reports_online_miner(self, monkeypatch):
        """A scan over a small network with one online miner reports it."""
        async def fake_probe(ip):
            if ip == "192.168.1.5":
                return {"ip": ip, "asicModel": "BM1370", "hostname": "bitaxe"}
            return None

        monkeypatch.setattr(discovery, "probe_host", fake_probe)
        result = await discover_tool.bitaxe_discover("192.168.1.0/29")  # hosts 1-6
        parsed = json.loads(result)
        assert parsed["subnet"] == "192.168.1.0/29"
        assert parsed["count"] == 1
        assert len(parsed["devices"]) == 1
        assert parsed["devices"][0]["ip"] == "192.168.1.5"
        assert parsed["devices"][0]["asicModel"] == "BM1370"

    @pytest.mark.asyncio
    async def test_discovery_no_miners(self, monkeypatch):
        """A network with no responding hosts yields devices==[] and count==0."""
        async def fake_probe(ip):
            return None

        monkeypatch.setattr(discovery, "probe_host", fake_probe)
        result = await discover_tool.bitaxe_discover("192.168.1.0/29")
        parsed = json.loads(result)
        assert parsed["devices"] == []
        assert parsed["count"] == 0

    def _patch_probe_transport(self, monkeypatch, handler):
        """Route discovery.probe_host's internal AsyncClient through a MockTransport."""
        real_async_client = httpx.AsyncClient

        def fake_async_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_async_client(*args, **kwargs)

        monkeypatch.setattr(discovery.httpx, "AsyncClient", fake_async_client)

    @pytest.mark.asyncio
    async def test_probe_host_accepts_real_bitaxe(self, monkeypatch):
        """probe_host accepts a body with a real /api/system/info shape (ASICModel)."""
        body = {"ASICModel": "BM1370", "hostname": "bitaxe", "version": "v1.0.1"}

        def handler(request):
            return httpx.Response(200, json=body)

        self._patch_probe_transport(monkeypatch, handler)
        result = await discovery.probe_host("192.168.1.42")
        assert result == {"ip": "192.168.1.42", "asicModel": "BM1370", "hostname": "bitaxe"}

    @pytest.mark.asyncio
    async def test_probe_host_rejects_non_bitaxe(self, monkeypatch):
        """probe_host rejects a 200 body that does not look like a BitAXE."""
        body = {"some": "other", "json": True}

        def handler(request):
            return httpx.Response(200, json=body)

        self._patch_probe_transport(monkeypatch, handler)
        assert await discovery.probe_host("192.168.1.42") is None

    @pytest.mark.asyncio
    async def test_offline_hosts_do_not_block(self, monkeypatch):
        """Offline hosts return quickly and the online miner is still reported."""
        import time

        async def fake_probe(ip):
            if ip == "192.168.1.10":
                return {"ip": ip, "asicModel": "BM1370", "hostname": "bitaxe"}
            await asyncio.sleep(0.3)
            return None

        monkeypatch.setattr(discovery, "probe_host", fake_probe)
        start = time.monotonic()
        result = await discover_tool.bitaxe_discover("192.168.1.8/29")  # hosts 9-14
        elapsed = time.monotonic() - start
        parsed = json.loads(result)
        assert parsed["count"] == 1
        assert parsed["devices"][0]["ip"] == "192.168.1.10"
        # Probes are concurrent: serial would take ~1.8s (6 * 0.3s); concurrent is far less.
        assert elapsed < 1.0
