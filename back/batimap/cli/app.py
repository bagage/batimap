from batimap.db import get_db
from batimap.extensions import batimap
from batimap.tasks.common import task_initdb
from flask import Blueprint, g

import click

bp = Blueprint('app_cli', __name__, cli_group=None)

@bp.cli.command("initdb")
@click.argument("departments", nargs=-1)
def initdb_command(departments):
    """
    Creates required tables in PostgreSQL server.
    """
    task_initdb(departments or get_db().get_departments())


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
        for city in batimap.stats(names_or_insees=items, force=not fast, refresh_cadastre_state=not fast):
            click.echo("{}: date={}".format(city, city.import_date))
    else:
        if all:
            click.echo("Will stats ALL available cities")
            d = get_db().get_departments()
        else:
            click.echo(f"Will stats given departments {items}")
            d = items
        for department in d:
            for city in batimap.stats(department=department, force=not fast, refresh_cadastre_state=not fast):
                click.echo("{}: date={}".format(city, city.import_date))
