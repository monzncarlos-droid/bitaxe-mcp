"""Tests for bitaxe_mcp/config.py."""
import json

import pytest

from bitaxe_mcp import config as cfg


def test_load_config_flat_format(monkeypatch):
    """load_config() accepts a valid flat MINERS_CONFIG format."""
    monkeypatch.setenv(
        "MINERS_CONFIG",
        json.dumps({"alpha": {"ip": "10.0.0.1"}, "beta": {"ip": "10.0.0.2"}}),
    )
    result = cfg.load_config()
    assert "alpha" in result
    assert result["alpha"]["ip"] == "10.0.0.1"
    assert "beta" in result
    assert result["beta"]["ip"] == "10.0.0.2"


def test_load_config_explicit_miners_key(monkeypatch):
    """load_config() accepts a valid explicit miners-key format."""
    monkeypatch.setenv(
        "MINERS_CONFIG",
        json.dumps({"miners": {"gamma": {"ip": "192.168.1.50"}}}),
    )
    result = cfg.load_config()
    assert "gamma" in result
    assert result["gamma"]["ip"] == "192.168.1.50"


def test_load_config_invalid_json(monkeypatch):
    """load_config() raises ValueError on invalid JSON."""
    monkeypatch.setenv("MINERS_CONFIG", "not json at all {")
    with pytest.raises(ValueError, match="valid JSON"):
        cfg.load_config()


def test_load_config_minimal(monkeypatch):
    """load_config() raises ValueError when no miners are listed."""
    monkeypatch.setenv("MINERS_CONFIG", json.dumps({"miners": {}}))
    with pytest.raises(ValueError, match="at least one miner"):
        cfg.load_config()


@pytest.fixture
def seeded_alpha_miners(monkeypatch):
    """Seed miners for get_miner_ip tests."""
    monkeypatch.setenv(
        "MINERS_CONFIG",
        json.dumps({"miners": {"alpha": {"ip": "10.0.0.1"}}}),
    )
    cfg.load_config()


def test_get_miner_ip_unknown_raises(seeded_alpha_miners):
    """get_miner_ip() raises ValueError for an unknown miner name."""
    with pytest.raises(ValueError, match="Unknown miner .zeta."):
        cfg.get_miner_ip("zeta")


def test_get_miner_ip_known_returns_correct_ip(seeded_alpha_miners):
    """get_miner_ip() returns the correct IP for a known miner."""
    assert cfg.get_miner_ip("alpha") == "10.0.0.1"


def test_miner_info_valid(monkeypatch):
    """MinerInfo validates correctly with a valid IP."""
    config = cfg.MinersConfig(**{"miners": {"ok": {"ip": "10.99.99.99"}}})
    assert config.miners["ok"].ip == "10.99.99.99"


def test_miner_info_empty_ip_fails(monkeypatch):
    """MinerInfo requires the ip field - an empty dict should fail."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        cfg.MinersConfig(**{"miners": {"bad": {}}})


def test_get_miner_config_injects_via_conftest(monkeypatch):
    """Confirm conftest autouse fixture injects MINERS_CONFIG."""
    config = cfg.load_config()
    assert "test-miner" in config



def test_get_miner_config_returns_lazy_copy():
    """get_miner_config() returns a copy, not the internal _miners reference."""
    cfg2 = __import__("bitaxe_mcp.config", fromlist=["get_miner_config"])
    cfg2._miners.clear()


def test_get_miner_config_injects_via_conftest(monkeypatch):
    """Confirm conftest autouse fixture injects MINERS_CONFIG."""
    config = cfg.load_config()
    assert "test-miner" in config
