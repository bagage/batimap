from batimap.extensions import batimap, db, odcadastre
from batimap.tasks.common import task_initdb
from flask import Blueprint, g

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
            click.echo("{}: date={}".format(city, city.import_date))
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
                click.echo("{}: date={}".format(city, city.import_date))


@bp.cli.command("cadastre")
@click.argument("cities", nargs=-1)
@click.option("--all", is_flag=True)
def initdb_command(cities, all):
    """
    Store cadastre stats in DB for given cities.
    """
    insees = [x.insee for x in db.get_cities()] if all else cities
    for insee in insees:
        c = odcadastre.compute_count(insee)
        click.echo(c)
