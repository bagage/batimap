import json

from batimap.taskdto import TaskDTO
from batimap.tasks.utils import list_tasks
from celery.result import AsyncResult
from flask import jsonify

from .routes import bp


@bp.route("/tasks/<uuid:task_id>", methods=["GET"])
def api_tasks_status(task_id):
    # task_id could be wrong, but we can not check it
    task = AsyncResult(str(task_id))
    current_app.logger.debug(f"Check status of {task_id} => {task.status}")
    try:
        result = json.loads(task.result) if task.result else None
    except Exception:
        result = {"error": f"Task failed: {task.result}"}
    response = {"state": task.state, "result": result}

    return jsonify(response)


@bp.route("/tasks", methods=["GET"])
def api_tasks():
    return jsonify([TaskDTO(t) for t in list_tasks()])
