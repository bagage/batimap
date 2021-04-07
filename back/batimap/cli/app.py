from pathlib import Path
from batimap.extensions import batimap, db, odcadastre
from batimap.tasks.common import task_initdb
from flask import Blueprint
import click

bp = Blueprint("app_cli", __name__, cli_group=None)


@bp.cli.command("initdb")
@click.argument("insees", nargs=-1)
def initdb_command(insees):
    """
    Fetch OSM and Cadastre data for given departments/cities INSEE.
    """
    task_initdb(insees or db.get_departments())


@bp.cli.command("stats")
@click.argument("items", nargs=-1)
@click.option("--fast", is_flag=True)
@click.option("--all", is_flag=True)
def get_city_stats(items, fast, all):
    """
    Returns cadastral status of given items.
    If status is unknown, it is computed first.
    """
    are_depts = len([x for x in items if len(x) < 4]) > 0
    if not all and not are_depts:
        click.echo(f"Will stats given cities {items}")
        for city in batimap.stats(
            names_or_insees=items, force=not fast, refresh_cadastre_state=not fast
        ):
            click.echo(f"{city}: date={city.import_date} bati={city.buildings}")
    else:
        if all:
            click.echo("Will stats ALL available cities")
            d = db.get_departments()
        else:
            click.echo(f"Will stats given departments {items}")
            d = items
        for department in d:
            for city in batimap.stats(
                department=department, force=not fast, refresh_cadastre_state=not fast
            ):
                click.echo(f"{city}: date={city.import_date} bati={city.buildings}")


@bp.cli.command("cadastre")
@click.argument("cities", nargs=-1)
@click.option("--all", is_flag=True)
def cadastre_command(cities, all):
    """
    Store cadastre stats in DB for given cities.
    """
    if not all and not len(cities):
        click.echo("Missing cities argument or --all flag!")
        return

    clear = []

    insees = [x.insee for x in db.get_cities()] if all else cities
    click.echo(f"Will stats given insees {', '.join(insees)}")
    for insee in insees:
        c = odcadastre.compute_count(insee)
        if c:
            click.echo(c)
            clear.append(insee)
        else:
            click.echo(
                f"couldn't compute count for {insee}, it is a valid INSEE and/or imported in DB?"
            )
    if all:
        initdb_is_done_file = Path("tiles/initdb_is_done")
        initdb_is_done_file.touch()
    else:
        for insee in clear:
            batimap.clear_tiles(insee)
