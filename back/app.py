#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gevent.monkey

gevent.monkey.patch_all()

import click
import logging
import os
from pathlib import Path
import json

from flask import Flask, request, Response, url_for
from flask_restful import inputs
from flask_cors import CORS

from celery import Celery
from celery.result import AsyncResult

from batimap import Batimap
from city import City
from citydto import CityEncoder, CityDTO
from overpassw import Overpass
from db_utils import Postgis

app = Flask(__name__)
app.config.from_pyfile(app.root_path + "/app.conf")
CORS(app)


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"], backend=app.config["CELERY_BACK_URL"])
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


def task_progress(task, current):
    current = int(current * 100) / 100  # round to 2 digits
    if task.request.id:
        task.update_state(state="PROGRESS", meta=json.dumps({"current": current, "total": 100}))
    else:
        LOG.warning(f"Task id not set, cannot update its progress to {current}%")


@celery.task(bind=True)
def task_initdb(self, items):
    items_are_cities = len([1 for x in items if len(x) > 3]) > 0
    if items_are_cities:
        departments = list(set([City(db, insee).department for insee in items]))
        departments = sorted([d for d in departments if d is not None])
    else:
        departments = items
    LOG.debug(f"Will run initdb on departments {departments}")

    initdb_is_done_file = Path("tiles/initdb_is_done")
    migration_file = Path("html/maintenance.html")
    if initdb_is_done_file.exists():
        initdb_is_done_file.unlink()
    if migration_file.exists():
        migration_file.unlink()

    # fill table with cities from cadastre website
    for d in batimap.update_departments_raster_state(db, departments):
        task_progress(self, d / len(departments) * 33)
    for d in batimap.fetch_departments_osm_state(db, departments):
        task_progress(self, 33 + d / len(departments) * 33)
    for d in db.import_city_stats_from_osmplanet(items):
        task_progress(self, 66 + d / len(items) * 33)

    initdb_is_done_file.touch()
    task_progress(self, 100)


@celery.task(bind=True)
def task_josm_data(self, insee):
    task_progress(self, 1)
    c = City(db, insee)
    # force refreshing cadastre date
    next(batimap.fetch_departments_osm_state(db, [c.department]))
    c = City(db, insee)
    is_ready = c.is_josm_ready()
    if not is_ready:
        # first, generate cadastre data for that city
        for d in batimap.fetch_cadastre_data(c):
            task_progress(self, d / 100 * 80)
        task_progress(self, 80)
        next(batimap.fetch_departments_osm_state(db, [c.department]))
    task_progress(self, 90)
    result = batimap.josm_data(db, insee, op)
    task_progress(self, 95)
    if c.get_last_import_date() != result["date"] or not is_ready:
        batimap.clear_tiles(db, insee)
    task_progress(self, 99)
    return json.dumps(result)


@celery.task(bind=True)
def task_update_insee_list(self, insee):
    (_, date) = next(batimap.stats(db, op, cities=[insee], force=False))
    task_progress(self, 50)
    (city, date2) = next(batimap.stats(db, op, cities=[insee], force=True))
    task_progress(self, 99)

    if date != date2:
        batimap.clear_tiles(db, insee)
    task_progress(self, 100)

    return json.dumps(CityDTO(date2, city), cls=CityEncoder)


LOG = logging.getLogger(__name__)

verbosity = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    level=verbosity[
        os.environ.get("BATIMAP_VERBOSITY")
        or app.config["VERBOSITY"]
        or ("DEBUG" if app.config["DEBUG"] else "CRITICAL")
    ],
)
batimap = Batimap()

db = Postgis(
    app.config["DB_NAME"],
    app.config["DB_USER"],
    app.config["DB_PASSWORD"],
    app.config["DB_PORT"],
    app.config["DB_HOST"],
    app.config["TILESERVER_URI"],
    batimap,
)

db.create_tables()

op = Overpass(app.config["OVERPASS_URI"])

# ROUTES


@app.route("/status", methods=["GET"])
def api_status() -> dict:
    return json.dumps(db.get_dates_count())


@app.route("/status/<department>", methods=["GET"])
def api_department_status(department) -> str:
    return json.dumps(
        [
            {x[0].insee: x[1]}
            for x in batimap.stats(db, op, department=department, force=request.args.get("force", False))
        ]
    )


@app.route("/status/<department>/<city>", methods=["GET"])
def api_city_status(department, city) -> str:
    for (city, date) in batimap.stats(
        db, op, cities=[city], force=request.args.get("force", default=False, type=inputs.boolean)
    ):
        return json.dumps({city.insee: date})
    return ""


@app.route("/status/by_date/<date>")
def api_cities_for_date(date) -> str:
    return json.dumps(db.get_cities_for_date(date))


@app.route("/insee/<insee>", methods=["GET"])
def api_insee(insee) -> dict:
    color_city = db.get_insee(insee)
    return json.dumps(color_city)


@app.route("/cities/in_bbox/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_color(lonNW, latNW, lonSE, latSE) -> dict:
    cities = db.get_cities_in_bbox(float(lonNW), float(latNW), float(lonSE), float(latSE))
    return json.dumps(cities, cls=CityEncoder)


@app.route("/legend/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    return json.dumps(db.get_legend_in_bbox(float(lonNW), float(latNW), float(lonSE), float(latSE)))


@app.route("/departments", methods=["GET"])
def api_departments() -> dict:
    return json.dumps(db.get_departments())


@app.route("/departments/in_bbox/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_departments_in_bbox(lonNW, latNW, lonSE, latSE) -> dict:
    departments = db.get_departments_in_bbox(float(lonNW), float(latNW), float(lonSE), float(latSE))
    return json.dumps(departments)


@app.route("/cities/obsolete", methods=["GET"])
def api_obsolete_city() -> dict:
    ignored = (request.args.get("ignored") or "").replace(" ", "").split(",")
    (city, position) = db.get_obsolete_city(ignored)
    return json.dumps({"position": [position.x, position.y], "city": city}, cls=CityEncoder)


@app.route("/cities/<insee>/update", methods=["GET"])
def api_update_insee_list(insee) -> dict:
    LOG.debug(f"Receive an update request for {insee}")

    new_task = task_update_insee_list.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}),
        status=202,
        headers={"Location": url_for("api_tasks_status", task_id=new_task.id)},
    )


@app.route("/cities/<insee>/josm", methods=["GET"])
def api_josm_data(insee) -> dict:
    LOG.debug(f"Receive an josm request for {insee}")
    new_task = task_josm_data.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}),
        status=202,
        headers={"Location": url_for("api_tasks_status", task_id=new_task.id)},
    )


@app.route("/initdb", methods=["POST"])
def api_initdb():
    items = request.get_json()["cities"]
    LOG.debug("Receive an initdb request for " + str(items))
    if items:
        new_task = task_initdb.delay(items)
        return Response(
            response=json.dumps({"task_id": new_task.id}),
            status=202,
            headers={"Location": url_for("api_tasks_status", task_id=new_task.id)},
        )
    return Response(status=400)


@app.route("/tasks/<task_id>", methods=["GET"])
def api_tasks_status(task_id):
    # task_id could be wrong, but we can not check it
    task = AsyncResult(task_id)
    LOG.debug(f"Check status of {task_id} => {task.status}")
    try:
        result = json.loads(task.result) if task.result else None
    except Exception:
        result = {"error": f"Task failed: {task.result}"}
    response = {"state": task.state, "result": result}

    return json.dumps(response, cls=CityEncoder)


# CLI
@app.cli.command("initdb")
@click.argument("departments", nargs=-1)
def initdb_command(departments):
    """
    Creates required tables in PostgreSQL server.
    """
    task_initdb(departments or db.get_departments())


@app.cli.command("update")
@click.argument("insee")
def update_command(insee):
    click.echo(task_update_insee_list(insee))


@app.cli.command("stats")
@click.argument("items", nargs=-1)
@click.option("--fast", is_flag=True)
@click.option("--all", is_flag=True)
def get_city_stats(items, fast, all):
    """
    Returns cadastral status of given items.
    If status is unknown, it is computed first.
    """
    d = []
    c = []
    if all:
        click.echo("Will stats ALL available cities")
        d = db.get_departments()
    else:
        are_depts = len([x for x in items if len(x) < 4]) > 0
        if are_depts:
            click.echo(f"Will stats given departments {items}")
            d = items
        else:
            click.echo(f"Will stats given cities {items}")
            c = items

    for department in d:
        for (city, date) in batimap.stats(
            db, op, department=department, cities=c, force=not fast, refresh_cadastre_state=not fast
        ):
            click.echo("{}: date={}".format(city, date))
