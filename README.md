# bitaxe-mcp

A single-process [MCP](https://modelcontextprotocol.io/) server for monitoring and configuring
[BitAXE](https://www.minebeecool.com/) Bitcoin ASIC miners. Shipped as the installable
`bitaxe-mcp` distribution (`import bitaxe_mcp`) — exposes tool functions that proxy HTTP
requests to miner APIs, no boilerplate, no framework weight.

## Features

- **Monitor** miner stats, ASIC capabilities, system info, and WiFi networks in real time
- **Configure** pools, fans, frequency/voltage, display settings, and more via generic patch tools
- **Maintain** miners remotely with restart and identify functions
- **Docker-ready** — multi-stage build + host-network deployment for LAN-located miners

## Architecture

```
bitaxe-mcp/
├── src/
│   └── bitaxe_mcp/    # importable package (shipped in the wheel)
│       ├── __init__.py    # docstring + __version__ (from installed metadata)
│       ├── config.py      # MINERS_CONFIG env parser (pydantic), IP resolution, cache
│       ├── client.py      # _http_request() helper, _format_json, timeout constants
│       ├── discovery.py   # subnet detection + concurrent LAN host probing
│       ├── server.py      # FastMCP instance, lifespan, main() entry point
│       └── tools/         # @mcp.tool() functions grouped by domain
│           ├── monitor.py     # status, stats, asic_info, scan_wifi (GET)
│           ├── configure.py   # configure, set_fan, set_frequency (PATCH)
│           ├── pool.py        # set_pool (PATCH)
│           ├── maintenance.py # restart, identify, list_miners (POST/config)
│           └── discover.py    # discover (LAN scan)
├── .env.example       # Example environment configuration
├── pyproject.toml     # uv project manifest — deps, dev-deps, pytest config, build backend
├── tests/
│   ├── conftest.py    # autouse fixtures: mock transport, seeded miners
│   ├── test_config.py # config parsing and validation (8 cases)
│   └── test_server.py # all 12 tool functions + error paths (40+ cases)
├── Dockerfile         # multi-stage build (builder → slim runtime)
├── docker-compose.yml # host-network deployment, env file bind
└── AGENTS.md          # Open-code agent instructions (architecture, gotchas, endpoints table)
```

**Key design**: tools call `bitaxe_mcp.client._http_request()` to construct URLs and manage
`AsyncClient` lifecycle. There is no router or middleware — each tool is a standalone async
function wired via `@mcp.tool()` on the single shared FastMCP instance in `bitaxe_mcp.server`.

## Installation

Requires: Python ≥3.12, [uv](https://github.com/astral-sh/uv) (recommended) or pip.

```bash
# From a source checkout
git clone <repo-url> && cd bitaxe-mcp

# Install into a venv (dependencies + the package itself); creates .venv with uv
uv sync                # uv
uv pip install .       # uv without the project layout
pip install .          # pip

# Or from a pre-built wheel
pip install dist/bitaxe_mcp-0.1.0-py3-none-any.whl

# Build a wheel + sdist from source
uv build
```

Installing the package provides the `bitaxe_mcp` import plus the `bitaxe-mcp` console command,
and the `import bitaxe_mcp` API surface (`bitaxe_mcp.config`, `bitaxe_mcp.client`,
`bitaxe_mcp.discovery`, `bitaxe_mcp.tools`, `bitaxe_mcp.server`).

## Configuration

Create `.env` from the example and add your miners:

```bash
cp .env.example .env
# edit .env → update MINERS_CONFIG
```

The `MINERS_CONFIG` environment variable is a JSON dict mapping miner names to their LAN IP addresses.
Both formats are accepted:

```bash
# Flat format (auto-wrapped into miners key)
MINERS_CONFIG='{"alpha-1":{"ip":"10.0.0.1"},"beta-1":{"ip":"10.0.0.2"}}'

# Explicit miners key
MINERS_CONFIG='{"miners":{"alpha-1":{"ip":"10.0.0.1"}}}'
```

## Running

### Local

The server runs in stdio transport mode — clients connect via the MCP SDK:

```bash
bitaxe-mcp                # console command from an installed package
python -m bitaxe_mcp.server # equivalent, from a source checkout or venv
```

On startup, `server_lifespan()` loads and validates `MINERS_CONFIG`. If config is missing or empty
a `ValueError` is raised at first tool call (not at import). The server itself starts cleanly either way.

### Via uvx / uv tool

[uvx](https://github.com/astral-sh/uv) can install the package into an ephemeral environment and
run the `bitaxe-mcp` console command in one step — no persistent installation required:

```bash
# From a local directory or git URL (works today, no publishing required)
MINERS_CONFIG='{"alpha-1":{"ip":"10.0.0.1"}}' uvx --from . bitaxe-mcp
MINERS_CONFIG='{"alpha-1":{"ip":"10.0.0.1"}}' uvx --from git+https://github.com/nuxnik/bitaxe-mcp bitaxe-mcp

# From a published package (once available on your package index)
MINERS_CONFIG='{"alpha-1":{"ip":"10.0.0.1"}}' uvx bitaxe-mcp
```

> `uvx` does not load `.env` files — provide `MINERS_CONFIG` directly on the command line
> (as above), via `direnv`/shell exports, or by passing it before the command.

### Docker

```bash
docker compose up --build
```

The container uses `network_mode: host` to reach miners on the local LAN.

## MCP Tools

| Tool | Method | Purpose |
|------|--------|---------|
| `bitaxe_status(miner)` | GET `/api/system/info` | Full system info (model, hash rate, temp, fan speed) |
| `bitaxe_stats(miner,\n  columns?)` | GET `/api/system/statistics?columns=...` | Statistics — hashrate, power, temperature. Pass column names like `["hashrate","power"]` |
| `bitaxe_asic_info(miner)` | GET `/api/system/asic` | ASIC capabilities: model, default frequency, voltage/frequency options |
| `bitaxe_scan_wifi(miner)` | GET `/api/system/wifi/scan` | Available WiFi networks near the miner |
| `bitaxe_configure(miner,\n  settings)` | PATCH `/api/system` | Generic — apply arbitrary key-value pairs to any setting group below |
| `bitaxe_set_fan(miner,\n  fanspeed?,\n  autofanspeed?)` | PATCH `/api/system` | Set fan speed (0–100%) or toggle auto-fan mode |
| `bitaxe_set_frequency(miner,\n  frequency,\n  core_voltage)` | PATCH `/api/system` | Overclock ASIC: set frequency + core voltage (auto-enables overclock) |
| `bitaxe_set_pool(miner,\n  url,\n  port?,\n  user?,\n  fallback_url?,\n  ...)` | PATCH `/api/system` | Configure primary and/or fallback BTC stratum pool |
| `bitaxe_restart(miner)` | POST `/api/system/restart` | Remote reboot the miner |
| `bitaxe_identify(miner)` | POST `/api/system/identify` | Blink front-panel LED / beep to locate a physical miner |
| `bitaxe_discover(subnet?)` | GET `/api/system/info` (per host) | Scan the LAN for active BitAXE devices; optional CIDR (e.g. `192.168.1.0/24`), defaults to the host's own subnet. Returns `{ "subnet", "count", "devices": [{ "ip", "asicModel", "hostname" }] }` |

### Settings groups (for `bitaxe_configure`)

- **Pool**: `stratumURL`, `stratumPort`, `stratumUser`, `stratumPassword`, `fallbackStratumURL`, ...
- **WiFi**: `ssid`, `wifiPass`, `hostname`
- **ASIC**: `coreVoltage`, `frequency`, `overclockEnabled`
- **Fan**: `autofanspeed`, `fanspeed`, `temptarget`
- **Display**: `rotation`, `invertscreen`, `displayTimeout`
- **Advanced**: `overheat_mode`, `statsFrequency`

> Every tool returns a pretty-printed JSON string. `bitaxe_configure` wraps the response in
> `{ "applied": settings, "response": <miner-api.json> }` for auditability.

## Running Tests

Use the dedicated `run_tests.py` script to execute the test suite:

```bash
# Run all tests
./run_tests.py

# Verbose output
./run_tests.py -v

# Specific file
./run_tests.py tests/test_config.py

# Collect without running
./run_tests.py --collect-only

# With coverage
./run_tests.py --cov=bitaxe_mcp --cov-report=term-missing
```

The script passes all flags directly to pytest. No separate `uv run` command needed.

## Tests

Tests use `conftest.py` autouse fixtures: a seeded `MINERS_CONFIG` with one `"test-miner"` entry,
and a mocked HTTP transport (`mock_transport`) that returns canned JSON for all miner API paths.
Unknown miner names raise `ValueError` (from `config.get_miner_ip()`).

### Test coverage

| Module | Cases | What is tested |
|--------|-------|----------------|
| `test_config.py` | 9 | Flat/explicit config format, invalid JSON, empty miners, IP resolution, pydantic validation, conftest injection |
| `test_server.py` | 40+ | All 12 tools + parameter variants (fan ranges, pool required/optional fields, frequency body shape) + HTTP error status codes (`500`, `404`) + unknown miner path + discovery scans |

## Configuration Reference

| Env Var | Type | Description | Example |
|---------|------|-------------|---------|
| `MINERS_CONFIG` | JSON string | Maps miner names → `{ "ip": "..." }` | `'{"miners":{"alpha-1":{"ip":"10.0.0.1"}}}'` |

## Project Structure Reference

```
bitaxe-mcp/
├── src/bitaxe_mcp/    # The importable package — see Architecture tree above
├── .env.example       # Template for local development
├── pyproject.toml     # uv project config: deps, dev-deps, pytest settings
│                        — mcp[cli] + httpx + pydantic-settings + python-dotenv
│                        — dev: pytest + pytest-asyncio
│                        — hatchling build backend + bitaxe-mcp entry point
├── Dockerfile         # Multi-stage: builder installs via uv → slim runtime
├── docker-compose.yml # Single service: build ., host network, env_file .env
└── AGENTS.md          # Architecture & endpoints table for code agents
```

## Configuration Tool Reference

| Setting | Type | Description | Example |
|---------|------|-------------|---------|
| `stratumURL` | string | Primary pool URL | `"stratum+tcp://pool.btc.com"` |
| `stratumPort` | int | Primary pool port | `3333` |
| `stratumUser` | string | Pool worker name | `"worker1"` |
| `stratumPassword` | string | Pool password | `"x"` |
| `fallbackStratumURL` | string | Fallback pool URL | `"stratum+tcp://backup.com"` |
| `ssid` | string | WiFi SSID (1-32 chars) | `"MyNetwork"` |
| `wifiPass` | string | WiFi password (8-63 chars) | `"SecurePass123"` |
| `coreVoltage` | int | ASIC core voltage (mV) | `850` |
| `frequency` | int | ASIC frequency (MHz) | `600` |
| `overclockEnabled` | 0 or 1 | Enable/disable overclocking | `1` |
| `autofanspeed` | 0 or 1 | Automatic fan control | `1` |
| `fanspeed` | int | Manual fan speed % (0-100) | `75` |
| `rotation` | int | Display rotation (degree) | `90` |
| `displayTimeout` | int | Screen off after N min (-1=always on) | `-1` |

## Docker Reference

| Directive | Value | Description |
|-----------|-------|-------------|
| `build` | `.` | Multi-stage build from project root |
| `network_mode` | `host` | Required for LAN miner reachability |
| `env_file` | `.env` | Binds local .env into container |
| `restart` | `unless-stopped` | Auto-restart on crashes or host reboots |

## Troubleshooting Reference

| Problem | Cause | Resolution |
|---------|-------|------------|
| Miner unreachable | LAN firewall / wrong IP | Verify miner IP and port from your router |
| Config validation error | MINERS_CONFIG malformed | Run `python -c "import json; print(json.loads(os.environ['MINERS_CONFIG']))"` |
| Overclock fails | Miners must support frequency/voltage override hardware limits apply — check ASIC capabilities via `bitaxe_asic_info`) | Check your miner's supported voltage/frequency ranges |
| Docker not reaching miners | Missing host network mode | Ensure `network_mode: host` in docker-compose.yml |

## Git Reference

Standard git workflow. Commits are squashed; no history rewriting after push.

## Contributors Guide

To add a new tool, mirror the existing patterns in `src/bitaxe_mcp/tools/` closely — use
`client._http_request(...)` via the `bitaxe_mcp.client` module attribute, decorate with
`mcp.tool()` from `bitaxe_mcp.server`, and import the module from
`src/bitaxe_mcp/tools/__init__.py` so it registers on the shared FastMCP instance.

## Verified pool setup example

The `bitaxe_set_pool` tool accepts a separate Stratum host, port, worker and password. This example connects a configured miner to BTC PoW Lab:

```json
{
  "miner": "alpha",
  "url": "stratum.btcpowlab-pool.com",
  "port": 3333,
  "user": "YOUR_BITCOIN_MAINNET_ADDRESS.worker",
  "pass_": "x"
}
```

Use only a public Bitcoin mainnet receive address that you control. Never provide a seed phrase or private key. After applying the change, inspect the active pool and confirm that accepted shares increase before relying on the configuration.

Address statistics are available at `https://btcpowlab-pool.com/address/YOUR_BITCOIN_MAINNET_ADDRESS`.

BTC PoW Lab is operated by Power CM Software. Mining is probabilistic. Accepted work does not guarantee a block, reward, profit or recovery of cost.
