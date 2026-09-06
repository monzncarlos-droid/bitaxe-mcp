"""Static multi-miner configuration.

Parses MINERS_CONFIG from the environment as a JSON dict and validates
the structure with pydantic.  Fails fast at import/first-call if the
config is missing or malformed.
"""

from __future__ import annotations

import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, model_validator

load_dotenv()

class MinerInfo(BaseModel):
    """Single miner entry."""

    ip: str


class MinersConfig(BaseModel):
    """Top-level container for the MINERS_CONFIG JSON value.

    Accepts both formats::

        {"miners": {"alice": {"ip": "10.0.0.1"}}}
        {"alice": {"ip": "10.0.0.1"}}
    """

    miners: dict[str, MinerInfo] | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: dict) -> dict:
        if isinstance(data, dict) and "miners" not in data:
            return {"miners": data}
        return data


# Module-level cache populated by load_config().
_miners: dict[str, dict[str, str]] = {}


def load_config() -> dict[str, dict[str, str]]:
    """Load, validate and return ``{name: {"ip": "..."}}``."""
    raw = os.environ.get("MINERS_CONFIG", "{}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "MINERS_CONFIG must be valid JSON"
        ) from exc

    config = MinersConfig(**parsed)

    if not config.miners:
        raise ValueError(
            "MINERS_CONFIG must contain at least one miner"
        )

    global _miners
    _miners = {name: {"ip": info.ip} for name, info in config.miners.items()}
    return _miners


def get_miner_ip(miner: str) -> str:
    """Return the IP address for *miner*, raising on unknown names."""
    entry = _miners.get(miner)
    if entry is None:
        available = ", ".join(sorted(_miners.keys()))
        raise ValueError(
            f"Unknown miner '{miner}'.  Available miners: {available}"
        )
    return entry["ip"]


def validate() -> dict[str, dict[str, str]]:
    """Public entry-point -- alias for load_config."""
    return load_config()


def get_miner_config() -> dict[str, dict[str, str]]:
    """Return the parsed miner configuration (name → {"ip": …}).

    Loads config lazily if it has not been loaded yet.
    """
    if not _miners:
        load_config()
    return dict(_miners)
