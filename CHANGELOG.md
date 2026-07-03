# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-07-03

### Added
- `status` command — live power flow: PV, battery %, output, grid import, home load, today's solar kWh
- `devices` command — tabular list of all devices with type, status, battery SOC, PV input, output
- `energy [--days N]` command — daily energy totals (solar, battery charge/discharge, grid→home, home usage)
- `config` command — current schedule mode, AI EMS state, home load, backup reserve, SOC cutoffs
- `set-output <watts>` — set home load output power
- `set-soc [--min N] [--max N]` — set battery charge/discharge SOC cutoff thresholds
- `set-export [--on/--off] [--limit <watts>]` — configure grid export
- All read commands support `--json` for raw API output
- Credentials via `SOLIX_EMAIL`/`SOLIX_PASSWORD`/`SOLIX_COUNTRY` env vars or `.env` file; also accepts legacy `ANKERUSER`/`ANKERPASSWORD`/`ANKERCOUNTRY`
- `--version` flag
- `make venv` / `make install` / `make update` / `make clean` targets
