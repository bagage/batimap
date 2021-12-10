import json
import logging

from batimap.bbox import Bbox
from batimap.citydto import CityDTO
from batimap.extensions import batimap, db
from batimap.point import Point
from batimap.taskdto import TaskDTO
from batimap.tasks.common import (
    task_initdb,
    task_josm_data,
    task_josm_data_fast,
    task_update_insee,
)
from batimap.tasks.utils import find_task_id, list_tasks
from celery.result import AsyncResult
from flask import request, url_for, jsonify
from flask_restful import inputs
from flask_smorest import Blueprint, abort
from geojson import Feature, FeatureCollection

LOG = logging.getLogger(__name__)
bp = Blueprint("app_routes", __name__)


@bp.route("/status", methods=["GET"])
def api_status() -> str:
    return jsonify(
        [{"date": x[0], "count": x[1]} for x in db.get_imports_count_per_year()]
    )


@bp.route("/status/<department>", methods=["GET"])
def api_department_status(department) -> str:
    return jsonify(
        [
            {x.insee: x.import_date}
            for x in batimap.stats(
                department=department, force=request.args.get("force", False)
            )
        ]
    )


@bp.route("/status/<department>/<city>", methods=["GET"])
def api_city_status(department, city) -> str:
    for city in batimap.stats(
        names_or_insees=[city],
        force=request.args.get("force", default=False, type=inputs.boolean),
    ):
        return jsonify({city.insee: city.import_date})
    return ""


@bp.route("/status/by_date/<date>")
def api_cities_for_date(date) -> str:
    return jsonify(db.get_cities_for_year(date))


@bp.route("/insee/<insee>", methods=["GET"])
def api_insee(insee) -> dict:
    city = db.get_city_for_insee(insee)
    if city:
        geo = db.get_city_geometry(insee)[0]
        feature = Feature(
            properties={
                "name": f"{city.name} - {city.insee}",
                "date": city.import_date,
            },
            geometry=json.loads(geo),
        )
        return jsonify(
            FeatureCollection(feature)
        )  # fixme: no need for FeatureCollection here
    abort(404, message=f"no city {insee}")


@bp.route("/bbox/cities", methods=["POST"])
def api_bbox_cities() -> dict:
    bboxes = (request.get_json() or {}).get("bboxes")
    if not bboxes:
        abort(400, message="missing required bboxes")
    cities = set()
    for bbox in bboxes:
        bbox_cities = set(db.get_cities_for_bbox(Bbox(*bbox)))
        cities |= bbox_cities
    return jsonify(sorted([CityDTO(x) for x in cities]))


@bp.route("/legend/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    result = db.get_imports_count_for_bbox(
        Bbox(float(lonNW), float(latSE), float(lonSE), float(latNW))
    )
    total = sum([x[1] for x in result])

    return jsonify(
        [
            {
                "name": import_date,
                "count": count,
                "percent": round(count * 100.0 / total, 2),
            }
            for (import_date, count) in result
        ]
    )


@bp.route("/insees/<insee>/osm_id", methods=["GET"])
def api_city_osm_id(insee) -> dict:
    (osm_id,) = db.get_osm_id(insee)
    return str(osm_id)


@bp.route("/departments", methods=["GET"])
def api_departments() -> dict:
    return jsonify(db.get_departments())


@bp.route("/departments/<dept>", methods=["GET"])
def api_department(dept) -> dict:
    d = db.get_department(dept)
    s = dict(db.get_department_import_stats(dept))
    date = max(s, key=s.get)
    return jsonify({"name": d.name, "date": date, "insee": dept})


@bp.route("/departments/<dept>/details", methods=["GET"])
def api_department_details(dept) -> dict:
    stats = dict(db.get_department_import_stats(dept))
    simplified = sorted(
        [ids for city in db.get_department_simplified_buildings(dept) for ids in city]
    )
    return jsonify({"simplified": simplified, "dates": stats})


@bp.route("/cities/<insee>", methods=["GET"])
def api_city(insee) -> dict:
    return jsonify(CityDTO(db.get_city_for_insee(insee)))


@bp.route("/cities/<insee>/tasks", methods=["GET"])
def api_city_tasks(insee) -> dict:
    city_tasks = [TaskDTO(t) for t in list_tasks() if t["args"] == [insee]]
    return jsonify(city_tasks)


@bp.route("/cities/<insee>/update", methods=["GET"])
def api_update_insee_list(insee) -> dict:
    LOG.debug(f"Receive an update request for {insee}")

    task_id = find_task_id("batimap.tasks.common.task_update_insee", [insee])

    if task_id:
        LOG.info(f"Returning an already running update request for {insee}: {task_id}")
    else:
        # only create a new task if none already exists
        task_id = task_update_insee.delay(insee).id

    return (
        {"task_id": task_id},
        202,
        {"Location": url_for("app_routes.api_tasks_status", task_id=task_id)},
    )


@bp.route("/cities/<insee>/josm", methods=["GET"])
def api_josm_data(insee) -> dict:
    LOG.debug(f"Receive an josm request for {insee}")

    c = db.get_city_for_insee(insee)
    if c.is_raster:
        return "raster city, no josm data available", 400
    elif c.is_josm_ready():
        task_id = task_josm_data_fast.delay(insee).id
    else:
        task_id = find_task_id("batimap.tasks.common.task_josm_data", [insee])

        if task_id:
            LOG.info(
                f"Returning an already running josm request for {insee}: {task_id}"
            )
        else:
            # only create a new task if none already exists
            task_id = task_josm_data.delay(insee).id

    return (
        {"task_id": task_id},
        202,
        {"Location": url_for("app_routes.api_tasks_status", task_id=task_id)},
    )


@bp.route("/cities/obsolete", methods=["GET"])
def api_obsolete_city() -> dict:
    ignored = request.args.get("ignored", "").replace(" ", "").split(",")
    ignored_cities = request.args.get("ignored_cities", "").replace(" ", "").split(",")
    minratio = request.args.get("minratio", 0, float)

    result = db.get_obsolete_city(ignored, ignored_cities, minratio)
    if result:
        city = CityDTO(result.City)
        (osm_id,) = db.get_osm_id(city.insee)
        position = Point.from_pg(result.position)
        return jsonify(
            {"position": [position.x, position.y], "city": city, "osmid": osm_id}
        )
    return "no obsolete city found", 404


@bp.route("/initdb", methods=["POST"])
def api_initdb():
    items = (request.get_json() or {}).get("cities")

    if not items:
        return "missing items param", 400

    LOG.debug(f"Receive an initdb request for {', '.join(items)}")
    task_id = find_task_id("batimap.tasks.common.task_initdb", [items])

    if task_id:
        LOG.info(
            f"Returning an already running initdb request for {', '.join(items)}: {task_id}"
        )
    else:
        # only create a new task if none already exists
        task_id = task_initdb.delay(items).id

    return (
        {"task_id": task_id},
        202,
        {"Location": url_for("app_routes.api_tasks_status", task_id=task_id)},
    )


@bp.route("/tasks/<uuid:task_id>", methods=["GET"])
def api_tasks_status(task_id):
    # task_id could be wrong, but we can not check it
    task = AsyncResult(str(task_id))
    LOG.debug(f"Check status of {task_id} => {task.status}")
    try:
        result = json.loads(task.result) if task.result else None
    except Exception:
        result = {"error": f"Task failed: {task.result}"}
    response = {"state": task.state, "result": result}

    return jsonify(response)


@bp.route("/tasks", methods=["GET"])
def api_tasks():
    return jsonify([TaskDTO(t) for t in list_tasks()])
