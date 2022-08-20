import json

from batimap.extensions import celery
from flask import current_app


def task_progress(task, current):
    current = int(min(current, 100) * 100) / 100  # round to 2 digits

    if task.request.id:
        task.update_state(
            state="PROGRESS", meta=json.dumps({"current": current, "total": 100})
        )
    else:
        current_app.logger.warning(
            f"Task id not set, cannot update its progress to {current}%"
        )


def list_tasks():
    """
    Returns list of all active and pending tasks
    """
    inspect = celery.control.inspect()
    active = inspect.active()
    reserved = inspect.reserved()
    active_tasks = (
        [task for worker_tasks in active.values() for task in worker_tasks]
        if active
        else []
    )
    waiting_tasks = (
        [task for worker_tasks in reserved.values() for task in worker_tasks]
        if reserved
        else []
    )
    return active_tasks + waiting_tasks


def find_task_id(task_name, args):
    """
    Returns a task id based on a task name and associated args
    """
    for task in list_tasks():
        if task["name"] == task_name and task["args"] == args:
            current_app.logger.info(
                f"found a task with same context (name={task_name}, args={args})!"
            )
            return task["id"]

    return None
