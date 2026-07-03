import asyncio
import json

import click
from aiohttp import ClientSession
from anker_solix_api.api import AnkerSolixApi
from anker_solix_api.errors import AnkerSolixError
from dotenv import load_dotenv

load_dotenv()


@click.group()
@click.option("--email", envvar=["SOLIX_EMAIL", "ANKERUSER"], help="Anker account email")
@click.option("--password", envvar=["SOLIX_PASSWORD", "ANKERPASSWORD"], help="Anker account password")
@click.option("--country", envvar=["SOLIX_COUNTRY", "ANKERCOUNTRY"], default="DE", show_default=True, help="Country code")
@click.pass_context
def cli(ctx, email, password, country):
    """solix-cli — Anker Solix command-line interface."""
    ctx.ensure_object(dict)
    ctx.obj.update(email=email, password=password, country=country)


async def _fetch(creds):
    session = ClientSession()
    api = AnkerSolixApi(creds["email"], creds["password"], creds["country"], session)
    await api.async_authenticate()
    await api.update_sites()
    await api.update_device_details()
    return api, session


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Raw JSON output")
@click.pass_context
def status(ctx, as_json):
    """Show power system status."""
    asyncio.run(_status(ctx.obj, as_json))


async def _status(creds, as_json):
    try:
        api, session = await _fetch(creds)
    except AnkerSolixError as e:
        raise click.ClickException(str(e))
    async with session:
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
    try:
        api, session = await _fetch(creds)
    except AnkerSolixError as e:
        raise click.ClickException(str(e))
    async with session:
        if as_json:
            click.echo(json.dumps(api.devices, indent=2))
            return
        _print_devices(api.devices)


def _print_devices(devs):
    FMT = "{:<22} {:<28} {:<12} {:<9} {:<8} {:<8} {}"
    click.echo(FMT.format("SN", "Name", "Type", "Status", "Battery", "PV", "Output"))
    click.echo("-" * 96)
    for sn, dev in devs.items():
        name = (dev.get("name") or dev.get("alias") or "")
        dtype = dev.get("type", "")
        st = dev.get("status_desc", "")
        bat = dev.get("battery_soc")
        bat_s = f"{bat}%" if bat else "-"
        pv = dev.get("input_power") or dev.get("generate_power")
        pv_s = f"{pv}W" if pv and pv != "0" else "-"
        out = dev.get("output_power") or dev.get("grid_to_home_power")
        out_s = f"{out}W" if out and out != "0" else "-"
        click.echo(FMT.format(sn[:22], name[:28], dtype[:12], st[:9], bat_s, pv_s, out_s))
