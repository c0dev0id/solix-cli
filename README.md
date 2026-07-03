# solix-cli

Command-line interface for the Anker Solix 3 solar battery system.

Wraps [thomluther/anker-solix-api](https://github.com/thomluther/anker-solix-api) — an unofficial reverse-engineered client for the Anker cloud API. Not affiliated with Anker. API may change without notice.

## Setup

```sh
git clone --recurse-submodules <repo-url>
cd anker-solix
make venv
```

Copy `.env.example` to `.env` and fill in your credentials:

```sh
cp .env.example .env
```

```
SOLIX_EMAIL=your@email.com
SOLIX_PASSWORD=yourpassword
SOLIX_COUNTRY=DE
```

Then install the binary and man page:

```sh
make install
```

This puts `solix-cli` in `$HOME/python/solix-cli/bin/` and the man page in `$HOME/python/solix-cli/share/man/man1/`. Add both to your `PATH` and `MANPATH` respectively.

## Usage

Credentials are read from `.env` or environment variables. All commands also accept `--email`, `--password`, `--country` flags.

### Read

```sh
solix-cli status              # live power flow: PV, battery, grid, home
solix-cli devices             # all devices with current readings
solix-cli energy              # daily energy totals, last 7 days
solix-cli energy --days 30    # last 30 days
solix-cli config              # current schedule, SOC limits, mode
```

Add `--json` to any read command for raw JSON output.

### Write

```sh
solix-cli set-output 300               # set home load output to 300W
solix-cli set-soc --min 10 --max 90   # discharge cutoff 10%, charge cutoff 90%
solix-cli set-soc --min 15            # change only discharge cutoff
solix-cli set-export --on             # enable grid export
solix-cli set-export --off            # disable grid export
solix-cli set-export --on --limit 500 # enable with 500W cap
```

## Makefile targets

| Target | Description |
|---|---|
| `make venv` | Create `.venv` and install all dependencies |
| `make install` | Install `solix-cli` binary and man page to `$HOME/python/solix-cli/` |
| `make update` | Pull latest upstream library changes |
| `make clean` | Remove `.venv`, `build/`, and egg-info directories |
