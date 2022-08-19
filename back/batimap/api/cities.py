from batimap.citydto import CityDTO
from batimap.extensions import db
from batimap.point import Point
from batimap.taskdto import TaskDTO
from batimap.tasks.common import task_josm_data, task_josm_data_fast, task_update_insee
from batimap.tasks.utils import find_task_id, list_tasks
from flask import current_app, jsonify, request, url_for

from .routes import bp


@bp.route("/cities/<insee>", methods=["GET"])
def api_city(insee) -> dict:
    return jsonify(CityDTO(db.get_city_for_insee(insee)))


@bp.route("/cities/<insee>/tasks", methods=["GET"])
def api_city_tasks(insee) -> dict:
    city_tasks = [TaskDTO(t) for t in list_tasks() if t["args"] == [insee]]
    return jsonify(city_tasks)


@bp.route("/cities/<insee>/update", methods=["GET"])
def api_update_insee_list(insee) -> dict:
    current_app.logger.debug(f"Receive an update request for {insee}")

    task_id = find_task_id("batimap.tasks.common.task_update_insee", [insee])

    if task_id:
        current_app.logger.info(
            f"Returning an already running update request for {insee}: {task_id}"
        )
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
    current_app.logger.debug(f"Receive an josm request for {insee}")

    c = db.get_city_for_insee(insee)
    if c.is_raster:
        return "raster city, no josm data available", 400
    elif c.is_josm_ready():
        task_id = task_josm_data_fast.delay(insee).id
    else:
        task_id = find_task_id("batimap.tasks.common.task_josm_data", [insee])

        if task_id:
            current_app.logger.info(
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
