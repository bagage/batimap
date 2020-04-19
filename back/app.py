#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gevent.monkey
from geojson import Feature, FeatureCollection

gevent.monkey.patch_all()

import click
import logging
import os
from pathlib import Path
import json

from flask import Flask, request, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restful import inputs
from flask_cors import CORS

from celery import Celery
from celery.result import AsyncResult

from code.batimap import Batimap
from code.bbox import Bbox
from code.point import Point
from code.citydto import CityEncoder, CityDTO
from code.overpass import Overpass

app = Flask(__name__)
app.config.from_pyfile(app.root_path + "/app.conf")
CORS(app)

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
    level=verbosity[os.environ.get("BATIMAP_VERBOSITY") or app.config["VERBOSITY"] or ("DEBUG" if app.config["DEBUG"] else "CRITICAL")],
)
LOG = logging.getLogger(__name__)
sql = SQLAlchemy(app)
from code.db import Db

db = Db(sql)

overpass = Overpass()
batimap = Batimap(db, overpass)


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
    current = int(min(current, 100) * 100) / 100  # round to 2 digits
    if task.request.id:
        task.update_state(state="PROGRESS", meta=json.dumps({"current": current, "total": 100}))
    else:
        LOG.warning(f"Task id not set, cannot update its progress to {current}%")


@celery.task(bind=True)
def task_initdb(self, items):
    items_are_cities = len([1 for x in items if len(x) > 3]) > 0
    if items_are_cities:
        departments = list(set([db.get_city_for_insee(insee).department for insee in items]))
        departments = sorted([d for d in departments if d is not None])
        LOG.debug(f"Will run initdb on departments {departments} from cities {items}")
    else:
        departments = items
        LOG.debug(f"Will run initdb on departments {departments}")

    initdb_is_done_file = Path("tiles/initdb_is_done")
    migration_file = Path("html/maintenance.html")
    if initdb_is_done_file.exists():
        initdb_is_done_file.unlink()

    # fill table with cities from cadastre website
    p = 25
    for d in batimap.update_departments_raster_state(departments):
        task_progress(self, 0 * p + d / len(departments) * p)
    for d in batimap.fetch_departments_osm_state(departments):
        task_progress(self, 1 * p + d / len(departments) * p)
    for d in batimap.import_city_stats_from_osmplanet(items):
        task_progress(self, 2 * p + d / len(items) * p)
    unknowns = (
        [c for c in items if db.get_city_for_insee(c).import_date == "unknown"]
        if items_are_cities
        else [c.insee for c in db.get_unknown_cities(departments)]
    )
    for (d, total) in batimap.compute_date_for_undated_cities(unknowns):
        task_progress(self, 3 * p + d / total * p)
    db.session.commit()

    initdb_is_done_file.touch()
    if migration_file.exists():
        migration_file.unlink()

    task_progress(self, 100)


@celery.task(bind=True)
def task_josm_data(self, insee):
    task_progress(self, 1)
    c = db.get_city_for_insee(insee)
    # force refreshing cadastre date
    next(batimap.fetch_departments_osm_state([c.department]))
    c = db.get_city_for_insee(insee)
    must_generate_data = not c.is_josm_ready()
    if must_generate_data:
        # first, generate cadastre data for that city
        for d in batimap.fetch_cadastre_data(c):
            task_progress(self, 1 + d / 100 * 79)
        task_progress(self, 80)
        next(batimap.fetch_departments_osm_state([c.department]))
    task_progress(self, 90)
    result = batimap.josm_data(insee)
    task_progress(self, 95)
    # refresh tiles if import date has changed or josm data was generated
    if db.get_city_for_insee(insee).import_date != result["date"] or must_generate_data:
        batimap.clear_tiles(insee)
    task_progress(self, 99)
    return json.dumps(result)


@celery.task(bind=True)
def task_update_insee(self, insee):
    before = db.get_city_for_insee(insee)
    task_progress(self, 50)
    city = next(batimap.stats(names_or_insees=[insee], force=True))
    task_progress(self, 99)

    if city.import_date != before.import_date:
        batimap.clear_tiles(insee)
    task_progress(self, 100)

    return json.dumps(CityDTO(city), cls=CityEncoder)


# ROUTES
@app.route("/status", methods=["GET"])
def api_status() -> dict:
    return json.dumps(db.get_imports_count_per_year())


@app.route("/status/<department>", methods=["GET"])
def api_department_status(department) -> str:
    return json.dumps([{x.insee: x.import_date} for x in batimap.stats(department=department, force=request.args.get("force", False))])


@app.route("/status/<department>/<city>", methods=["GET"])
def api_city_status(department, city) -> str:
    for city in batimap.stats(names_or_insees=[city], force=request.args.get("force", default=False, type=inputs.boolean)):
        return json.dumps({city.insee: city.import_date})
    return ""


@app.route("/status/by_date/<date>")
def api_cities_for_date(date) -> str:
    return json.dumps(db.get_cities_for_year(date))


@app.route("/insee/<insee>", methods=["GET"])
def api_insee(insee) -> dict:
    city = db.get_city_for_insee(insee)
    if city:
        geo = db.get_city_geometry(insee)[0]
        feature = Feature(properties={"name": f"{city.name} - {city.insee}", "date": city.import_date}, geometry=json.loads(geo))
        return json.dumps(FeatureCollection(feature))  # fixme: no need for FeatureCollection here
    return f"no city {insee}", 404


@app.route("/bbox/cities", methods=["POST"])
def api_bbox_cities() -> dict:
    bboxes = (request.get_json() or {}).get("bboxes")
    cities = set()
    for bbox in bboxes:
        cities = cities | set(db.get_cities_for_bbox(Bbox(*bbox)))
    return json.dumps([CityDTO(x) for x in cities], cls=CityEncoder)


@app.route("/legend/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    result = db.get_imports_count_for_bbox(Bbox(float(lonNW), float(latSE), float(lonSE), float(latNW)))
    total = sum([x[1] for x in result])

    return json.dumps(
        [{"name": import_date, "count": count, "percent": round(count * 100.0 / total, 2)} for (import_date, count) in result]
    )


@app.route("/departments", methods=["GET"])
def api_departments() -> dict:
    return json.dumps(db.get_departments())


@app.route("/departments/<dept>", methods=["GET"])
def api_department_details(dept) -> dict:
    stats = dict(db.get_department_import_stats(dept))
    simplified = sorted([ids for city in db.get_department_simplified_buildings(dept) for ids in city])
    return json.dumps({"simplified": simplified, "dates": stats})


@app.route("/cities/obsolete", methods=["GET"])
def api_obsolete_city() -> dict:
    ignored = (request.args.get("ignored") or "").replace(" ", "").split(",")
    result = db.get_obsolete_city(ignored)
    if result:
        city = CityDTO(result.City)
        (osm_id,) = db.get_city_osm_id(city.insee)
        position = Point.from_pg(result.position)
        return json.dumps({"position": [position.x, position.y], "city": city, "osmid": osm_id}, cls=CityEncoder)


@app.route("/cities/<insee>/update", methods=["GET"])
def api_update_insee_list(insee) -> dict:
    LOG.debug(f"Receive an update request for {insee}")

    new_task = task_update_insee.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}), status=202, headers={"Location": url_for("api_tasks_status", task_id=new_task.id)},
    )


@app.route("/cities/<insee>/osm_id", methods=["GET"])
def api_city_osm_id(insee) -> dict:
    (osm_id,) = db.get_city_osm_id(insee)
    return str(osm_id)


@app.route("/cities/<insee>/josm", methods=["GET"])
def api_josm_data(insee) -> dict:
    LOG.debug(f"Receive an josm request for {insee}")
    new_task = task_josm_data.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}), status=202, headers={"Location": url_for("api_tasks_status", task_id=new_task.id)},
    )


@app.route("/initdb", methods=["POST"])
def api_initdb():
    items = (request.get_json() or {}).get("cities")
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


@app.cli.command("stats")
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
            d = db.get_departments()
        else:
            click.echo(f"Will stats given departments {items}")
            d = items
        for department in d:
            for city in batimap.stats(department=department, force=not fast, refresh_cadastre_state=not fast):
                click.echo("{}: date={}".format(city, city.import_date))
