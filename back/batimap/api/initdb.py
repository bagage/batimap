from batimap.tasks.common import task_initdb
from batimap.tasks.utils import find_task_id
from celery import current_app
from flask import request, url_for

from .routes import bp


@bp.route("/initdb", methods=["POST"])
def api_initdb():
    items = (request.get_json() or {}).get("cities")

    if not items:
        return "missing items param", 400

    current_app.logger.debug(f"Receive an initdb request for {', '.join(items)}")
    task_id = find_task_id("batimap.tasks.common.task_initdb", [items])

    if task_id:
        current_app.logger.info(
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
