# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`solix-cli` — a command-line interface for the Anker Solix 3 solar battery system. Wraps the unofficial [thomluther/anker-solix-api](https://github.com/thomluther/anker-solix-api) Python library (vendored as a git submodule at `vendor/anker-solix-api`).

## Dev Environment

```sh
make venv          # create .venv and install all deps
make install       # install solix-cli binary to $HOME/python/bin/
make update        # pull latest upstream library changes
make clean         # remove .venv
```

Activate with `.venv/bin/solix-cli` or `. .venv/bin/activate`.

Credentials go in `.env` (copy `.env.example`): `SOLIX_EMAIL`, `SOLIX_PASSWORD`, `SOLIX_COUNTRY`.

## Architecture

All code lives in `src/solix_cli/cli.py`. Entry point: `solix_cli.__main__:main`.

**`_connect(creds, details=False)`** — async context manager. Authenticates, calls `update_sites()` (always), and optionally `update_device_details()`. The `details=True` path is only needed for `config` since `update_sites()` already populates `api.devices` with live power data sufficient for all other commands.

**`_autoselect(api)`** — picks the first `SolixDeviceType.SOLARBANK` device from `api.devices`. Single-device assumption; returns `(site_id, device_sn)`.

**Commands:**

| Command | API calls | Notes |
|---|---|---|
| `status` | `update_sites()` | reads `api.sites` |
| `devices` | `update_sites()` | reads `api.devices` |
| `energy [--days N]` | `update_sites()` + `energy_daily()` | `dayTotals=True` |
| `config` | `update_sites()` + `update_device_details()` | schedule/SOC from device details cache |
| `set-output <W>` | `update_sites()` + `set_sb2_home_load()` | |
| `set-soc [--min N] [--max N]` | `update_sites()` + `set_power_cutoff()` | SB2/3 path, not `set_station_parm` |
| `set-export [--on/--off] [--limit W]` | `update_sites()` + `set_station_parm()` | may not work on all SB3 configs |

All commands support `--json` for raw API output. `--version` reads from package metadata.

## Platform

OpenBSD. Use `doas pkg_add -a` for missing system packages. Always use the virtualenv — never `pip install` globally.
