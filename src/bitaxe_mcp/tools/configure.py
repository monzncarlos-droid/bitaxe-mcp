"""Configuration tools (PATCH /api/system)."""

from __future__ import annotations

from bitaxe_mcp import client
from bitaxe_mcp.server import mcp


@mcp.tool()
async def bitaxe_configure(
    miner: str,
    settings: dict,
) -> str:
    """
    Send a generic PATCH to *miner*'s API with *settings*.
    Args:
        miner: the name of the miner to configure
        settings: is a dict of key-value pairs to apply.

    ## Settings can be any of the following:
    Pool Configuration:

        stratumURL - Primary stratum server URL (e.g., “stratum+tcp://pool.example.com”)
        stratumPort - Primary stratum server port (1-65535)
        stratumUser - Username for primary stratum server
        stratumPassword - Password for primary stratum server
        fallbackStratumURL - Fallback stratum server URL
        fallbackStratumPort - Fallback stratum server port (1-65535)
        fallbackStratumUser - Username for fallback stratum server
        fallbackStratumPassword - Password for fallback stratum server
        useFallbackStratum - Force use of fallback stratum pool

    WiFi Configuration:

        ssid - WiFi network SSID (1-32 characters)
        wifiPass - WiFi network password (8-63 characters)
        hostname - Device hostname (alphanumeric and hyphens only)

    ASIC Configuration:

        coreVoltage - ASIC core voltage in millivolts (requires overclockEnabled: 1)
        frequency - ASIC frequency in MHz (requires overclockEnabled: 1)
        overclockEnabled - Enable custom voltage/frequency (0=disabled, 1=enabled)

    Fan Control:

        autofanspeed - Automatic fan speed control (0=manual, 1=auto)
        fanspeed - Manual fan speed percentage when autofanspeed is disabled (0-100)
        temptarget - Target temperature in °C for automatic fan control (0-100)

    Display Settings:

        rotation - Screen rotation (0, 90, 180, 270 degrees)
        invertscreen - Invert screen colors (0=normal, 1=inverted)
        displayTimeout - Display timeout in minutes (-1=always on, 0=always off, >0=timeout)

    Advanced Settings:

        overheat_mode - Overheat protection mode (0=disabled)
        statsFrequency - Statistics logging frequency in seconds (0=disabled)
    """
    resp = await client._http_request("patch", miner, "/api/system", json=settings)
    resp.raise_for_status()
    return client._format_json({"applied": settings, "response": resp.json()})


@mcp.tool()
async def bitaxe_set_fan(
    miner: str,
    fanspeed: int | None = None,
    autofanspeed: bool | None = None,
) -> str:
    """
    Set the fan speed or enable automatic fan control on *miner*.
    Args:
        miner: the name of the miner to change the fan config of
        fanspeed: The percentage of the speed the fan should run - from 0 to 100
        autofanspeed: Whether the auto fan speed should be turned on or off.
    """
    if fanspeed is not None and not (0 <= fanspeed <= 100):
        raise ValueError("fanspeed must be 0 to 100")
    body: list = []
    if autofanspeed is True:
        body.append({"autofanspeed": 1})
    elif fanspeed is not None:
        body.append({"fanspeed": fanspeed})
    else:
        raise ValueError("Provide at least one of: fanspeed, autofanspeed")
    resp = await client._http_request("patch", miner, "/api/system", json=body)
    resp.raise_for_status()
    return client._format_json({"body": body, "response": resp.json()})


@mcp.tool()
async def bitaxe_set_frequency(
    miner: str,
    frequency: int,
    core_voltage: int,
) -> str:
    """Set ASIC frequency and core voltage on *miner*.
    Args:
        miner: the name of the miner to change the frequency of
        frequency: The frequency the ASIC should run at
        core_volage: The voltage at which the core should run.

    Overclocking is automatically enabled along with the change.
    """
    body = {
        "frequency": frequency,
        "coreVoltage": core_voltage,
        "overclockEnabled": 1,
    }
    resp = await client._http_request("patch", miner, "/api/system", json=body)
    resp.raise_for_status()
    return client._format_json({"applied": body, "response": resp.json()})
