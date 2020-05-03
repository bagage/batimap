from flask import request, Response, url_for
from flask_restful import inputs
from flask_smorest import abort, Blueprint
from geojson import Feature, FeatureCollection

from batimap.bbox import Bbox
from batimap.citydto import CityEncoder, CityDTO
from batimap.db import get_db
from batimap.extensions import batimap
from batimap.point import Point
from batimap.tasks.common import task_initdb, task_josm_data, task_update_insee

from celery.result import AsyncResult
from sqlalchemy.exc import IntegrityError

import click
import json
import logging

LOG = logging.getLogger(__name__)


bp = Blueprint('app_routes', __name__)

@bp.route("/status", methods=["GET"])
def api_status() -> dict:
    return json.dumps(get_db().get_imports_count_per_year())


@bp.route("/status/<department>", methods=["GET"])
def api_department_status(department) -> str:
    return json.dumps([{x.insee: x.import_date} for x in batimap.stats(department=department, force=request.args.get("force", False))])


@bp.route("/status/<department>/<city>", methods=["GET"])
def api_city_status(department, city) -> str:
    for city in batimap.stats(names_or_insees=[city], force=request.args.get("force", default=False, type=inputs.boolean)):
        return json.dumps({city.insee: city.import_date})
    return ""


@bp.route("/status/by_date/<date>")
def api_cities_for_date(date) -> str:
    return json.dumps(get_db().get_cities_for_year(date))


@bp.route("/insee/<insee>", methods=["GET"])
def api_insee(insee) -> dict:
    city = get_db().get_city_for_insee(insee)
    if city:
        geo = get_db().get_city_geometry(insee)[0]
        feature = Feature(properties={"name": f"{city.name} - {city.insee}", "date": city.import_date}, geometry=json.loads(geo))
        return json.dumps(FeatureCollection(feature))  # fixme: no need for FeatureCollection here
    abort(404, message=f"no city {insee}")


@bp.route("/bbox/cities", methods=["POST"])
# @bp.arguments(BBoxSchema, location='json')
def api_bbox_cities() -> dict:
    bboxes = (request.get_json() or {}).get("bboxes")
    cities = set()
    for bbox in bboxes:
        cities = cities | set(get_db().get_cities_for_bbox(Bbox(*bbox)))
    return json.dumps([CityDTO(x) for x in cities], cls=CityEncoder)


@bp.route("/legend/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    result = get_db().get_imports_count_for_bbox(Bbox(float(lonNW), float(latSE), float(lonSE), float(latNW)))
    total = sum([x[1] for x in result])

    return json.dumps(
        [{"name": import_date, "count": count, "percent": round(count * 100.0 / total, 2)} for (import_date, count) in result]
    )


@bp.route("/insees/<insee>/osm_id", methods=["GET"])
def api_city_osm_id(insee) -> dict:
    (osm_id,) = get_db().get_osm_id(insee)
    return str(osm_id)


@bp.route("/departments", methods=["GET"])
def api_departments() -> dict:
    return json.dumps(get_db().get_departments())


@bp.route("/departments/<dept>", methods=["GET"])
def api_department(dept) -> dict:
    d = get_db().get_department(dept)
    s = dict(get_db().get_department_import_stats(dept))
    date = max(s, key=s.get)
    return json.dumps({"name": d.name, "date": date, "insee": dept})


@bp.route("/departments/<dept>/details", methods=["GET"])
def api_department_details(dept) -> dict:
    stats = dict(get_db().get_department_import_stats(dept))
    simplified = sorted([ids for city in get_db().get_department_simplified_buildings(dept) for ids in city])
    return json.dumps({"simplified": simplified, "dates": stats})


@bp.route("/cities/<insee>", methods=["GET"])
def api_city(insee) -> dict:
    return json.dumps(CityDTO(get_db().get_city_for_insee(insee)), cls=CityEncoder)


@bp.route("/cities/<insee>/update", methods=["GET"])
def api_update_insee_list(insee) -> dict:
    LOG.debug(f"Receive an update request for {insee}")

    new_task = task_update_insee.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}), status=202, headers={"Location": url_for("app_routes.api_tasks_status", task_id=new_task.id)},
    )


@bp.route("/cities/<insee>/josm", methods=["GET"])
def api_josm_data(insee) -> dict:
    LOG.debug(f"Receive an josm request for {insee}")
    new_task = task_josm_data.delay(insee)
    return Response(
        response=json.dumps({"task_id": new_task.id}), status=202, headers={"Location": url_for("app_routes.api_tasks_status", task_id=new_task.id)},
    )


@bp.route("/cities/obsolete", methods=["GET"])
# @bp.arguments(BBoxSchema, location='json')
def api_obsolete_city() -> dict:
    ignored = (request.args.get("ignored") or "").replace(" ", "").split(",")
    result = get_db().get_obsolete_city(ignored)
    if result:
        city = CityDTO(result.City)
        (osm_id,) = get_db().get_osm_id(city.insee)
        position = Point.from_pg(result.position)
        return json.dumps({"position": [position.x, position.y], "city": city, "osmid": osm_id}, cls=CityEncoder)


@bp.route("/initdb", methods=["POST"])
# @bp.arguments(BBoxSchema, location='json')
def api_initdb():
    items = (request.get_json() or {}).get("cities")
    LOG.debug("Receive an initdb request for " + str(items))
    if items:
        new_task = task_initdb.delay(items)
        return Response(
            response=json.dumps({"task_id": new_task.id}),
            status=202,
            headers={"Location": url_for("app_routes.api_tasks_status", task_id=new_task.id)},
        )
    return Response(status=400)


@bp.route("/tasks/<task_id>", methods=["GET"])
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
