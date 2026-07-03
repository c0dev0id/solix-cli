import asyncio
import importlib.metadata
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import click
from aiohttp import ClientSession
from anker_solix_api.api import AnkerSolixApi
from anker_solix_api.apitypes import SolarbankUsageMode, SolixDeviceType
from anker_solix_api.errors import AnkerSolixError
from anker_solix_api.helpers import get_enum_name
from dotenv import load_dotenv

load_dotenv()


@click.group()
@click.option("--email", envvar=["SOLIX_EMAIL", "ANKERUSER"], help="Anker account email")
@click.option("--password", envvar=["SOLIX_PASSWORD", "ANKERPASSWORD"], help="Anker account password")
@click.option("--country", envvar=["SOLIX_COUNTRY", "ANKERCOUNTRY"], default="DE", show_default=True, help="Country code")
@click.version_option(importlib.metadata.version("solix-cli"), prog_name="solix-cli")
@click.pass_context
def cli(ctx, email, password, country):
    """solix-cli — Anker Solix command-line interface."""
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand and ctx.invoked_subcommand != "version":
        if not email or not password:
            raise click.UsageError(
                "Credentials required. Set SOLIX_EMAIL and SOLIX_PASSWORD (or use --email/--password)."
            )
    ctx.obj.update(email=email, password=password, country=country)


@asynccontextmanager
async def _connect(creds, details=False):
    async with ClientSession() as session:
        api = AnkerSolixApi(creds["email"], creds["password"], creds["country"], session)
        try:
            await api.async_authenticate()
            await api.update_sites()
            if details:
                await api.update_device_details()
        except AnkerSolixError as e:
            raise click.ClickException(str(e))
        yield api


def _autoselect(api):
    for sn, dev in api.devices.items():
        if dev.get("type") == SolixDeviceType.SOLARBANK.value:
            return dev["site_id"], sn
    raise click.ClickException("No solarbank device found")


def _kwh(val):
    try:
        return f"{float(val):.2f} kWh" if val else "-"
    except (ValueError, TypeError):
        return "-"


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def status(ctx, as_json):
    """Show live power system status."""
    asyncio.run(_status(ctx.obj, as_json))


async def _status(creds, as_json):
    async with _connect(creds) as api:
        if as_json:
            click.echo(json.dumps(api.sites, indent=2))
            return
        for site in api.sites.values():
            _print_site(site)


def _print_site(site):
    name = site.get("site_info", {}).get("site_name") or site.get("site_id", "?")
    click.echo(f"Site: {name}")
    sb = site.get("solarbank_info", {})
    if sb:
        pv = sb.get("total_photovoltaic_power", "0")
        out = sb.get("total_output_power", "0")
        bat = sb.get("total_battery_power", "?")
        click.echo(f"  PV {pv}W  Battery {bat}%  Output {out}W")
    grid_pwr = site.get("grid_info", {}).get("grid_to_home_power")
    home = site.get("home_load_power")
    if grid_pwr or home:
        click.echo(f"  Grid {grid_pwr or 0}W  Home {home or 0}W")
    solar_kwh = site.get("energy_details", {}).get("today", {}).get("solar_production")
    if solar_kwh:
        click.echo(f"  Today: {solar_kwh} kWh solar")
    click.echo()


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def devices(ctx, as_json):
    """List all devices with current readings."""
    asyncio.run(_devices(ctx.obj, as_json))


async def _devices(creds, as_json):
    async with _connect(creds) as api:
        if as_json:
            click.echo(json.dumps(api.devices, indent=2))
            return
        _print_devices(api.devices)


def _print_devices(devs):
    FMT = "{:<22} {:<28} {:<12} {:<9} {:<8} {:<8} {}"
    click.echo(FMT.format("SN", "Name", "Type", "Status", "Battery", "PV", "Output"))
    click.echo("-" * 96)
    for sn, dev in devs.items():
        name = dev.get("name") or dev.get("alias") or ""
        dtype = dev.get("type", "")
        st = dev.get("status_desc", "")
        bat = dev.get("battery_soc")
        bat_s = f"{bat}%" if bat else "-"
        pv = dev.get("input_power") or dev.get("generate_power")
        pv_s = f"{pv}W" if pv and pv != "0" else "-"
        out = dev.get("output_power") or dev.get("grid_to_home_power")
        out_s = f"{out}W" if out and out != "0" else "-"
        click.echo(FMT.format(sn[:22], name[:28], dtype[:12], st[:9], bat_s, pv_s, out_s))


@cli.command()
@click.option("--days", default=7, show_default=True, help="Number of past days")
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def energy(ctx, days, as_json):
    """Show daily energy totals."""
    asyncio.run(_energy(ctx.obj, days, as_json))


async def _energy(creds, days, as_json):
    async with _connect(creds) as api:
        site_id, sn = _autoselect(api)
        start = datetime.today() - timedelta(days=days - 1)
        data = await api.energy_daily(
            siteId=site_id,
            deviceSn=sn,
            startDay=start,
            numDays=days,
            dayTotals=True,
            devTypes={SolixDeviceType.SOLARBANK.value, SolixDeviceType.SMARTMETER.value},
        )
        if as_json:
            click.echo(json.dumps(data, indent=2))
            return
        _print_energy(data)


def _print_energy(data):
    FMT = "{:<12} {:>10} {:>10} {:>10} {:>12} {:>12}"
    click.echo(FMT.format("Date", "Solar", "Bat↑", "Bat↓", "Grid→Home", "Home"))
    click.echo("-" * 68)
    for day in data.values():
        click.echo(FMT.format(
            day.get("date", ""),
            _kwh(day.get("solar_production")),
            _kwh(day.get("battery_charge")),
            _kwh(day.get("battery_discharge")),
            _kwh(day.get("grid_to_home")),
            _kwh(day.get("home_usage")),
        ))


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def config(ctx, as_json):
    """Show current device configuration."""
    asyncio.run(_config(ctx.obj, as_json))


async def _config(creds, as_json):
    async with _connect(creds, details=True) as api:
        site_id, sn = _autoselect(api)
        dev = api.devices[sn]
        site = api.sites[site_id]
        if as_json:
            click.echo(json.dumps({
                "schedule": dev.get("schedule", {}),
                "power_cutoff": dev.get("power_cutoff_data", []),
                "site_details": site.get("site_details", {}),
            }, indent=2))
            return
        _print_config(dev, site)


def _print_config(dev, site):
    sched = dev.get("schedule", {})
    mode_name = get_enum_name(SolarbankUsageMode, sched.get("mode_type", 0), default="unknown")
    ai = sched.get("ai_ems") or {}
    click.echo(f"Mode:             {mode_name}")
    click.echo(f"AI EMS:           {'on' if ai.get('enable') else 'off'}")
    click.echo(f"Home load:        {sched.get('default_home_load', '?')}W")
    click.echo(f"Backup reserve:   {sched.get('reserved_soc', '?')}%")
    cutoffs = dev.get("power_cutoff_data") or []
    selected = next((c for c in cutoffs if c.get("is_selected")), None)
    if selected:
        click.echo(f"Discharge cutoff: {selected.get('output_cutoff_data', '?')}%")
        click.echo(f"Charge cutoff:    {selected.get('input_cutoff_data', '?')}%")
    grid_export = (site.get("site_details") or {}).get("grid_export")
    if grid_export is not None:
        click.echo(f"Grid export:      {'on' if grid_export else 'off'}")


@cli.command("set-output")
@click.argument("watts", type=int)
@click.pass_context
def set_output(ctx, watts):
    """Set home load output power (watts)."""
    asyncio.run(_set_output(ctx.obj, watts))


async def _set_output(creds, watts):
    async with _connect(creds) as api:
        site_id, sn = _autoselect(api)
        result = await api.set_sb2_home_load(siteId=site_id, deviceSn=sn, preset=float(watts))
        if result:
            click.echo(f"Home load set to {watts}W")
        else:
            raise click.ClickException("Command failed")


@cli.command("set-soc")
@click.option("--min", "soc_min", type=int, default=None, help="Discharge cutoff %")
@click.option("--max", "soc_max", type=int, default=None, help="Charge cutoff %")
@click.pass_context
def set_soc(ctx, soc_min, soc_max):
    """Set battery charge/discharge SOC limits."""
    if soc_min is None and soc_max is None:
        raise click.UsageError("Provide at least --min or --max")
    asyncio.run(_set_soc(ctx.obj, soc_min, soc_max))


async def _set_soc(creds, soc_min, soc_max):
    async with _connect(creds) as api:
        _, sn = _autoselect(api)
        result = await api.set_power_cutoff(deviceSn=sn, socMin=soc_min, socMax=soc_max)
        if result:
            parts = []
            if soc_min is not None:
                parts.append(f"discharge cutoff {soc_min}%")
            if soc_max is not None:
                parts.append(f"charge cutoff {soc_max}%")
            click.echo(f"SOC limits set: {', '.join(parts)}")
        else:
            raise click.ClickException("Command failed")


@cli.command("set-export")
@click.option("--on/--off", "enabled", default=None, help="Enable or disable grid export")
@click.option("--limit", type=int, default=None, help="Export cap in watts")
@click.pass_context
def set_export(ctx, enabled, limit):
    """Enable/disable grid export and set watt cap."""
    if enabled is None and limit is None:
        raise click.UsageError("Provide --on/--off and/or --limit")
    asyncio.run(_set_export(ctx.obj, enabled, limit))


async def _set_export(creds, enabled, limit):
    async with _connect(creds) as api:
        site_id, sn = _autoselect(api)
        result = await api.set_station_parm(
            siteId=site_id, deviceSn=sn,
            gridExport=enabled,
            gridExportLimit=limit,
        )
        if result:
            parts = []
            if enabled is not None:
                parts.append(f"grid export {'on' if enabled else 'off'}")
            if limit is not None:
                parts.append(f"cap {limit}W")
            click.echo(f"Export configured: {', '.join(parts)}")
        else:
            raise click.ClickException("Command failed (device may not support this setting)")
