import json
import logging
from batimap.extensions import celery


LOG = logging.getLogger(__name__)


def task_progress(task, current):
    current = int(min(current, 100) * 100) / 100  # round to 2 digits

    if task.request.id:
        task.update_state(
            state="PROGRESS", meta=json.dumps({"current": current, "total": 100})
        )
    else:
        LOG.warning(f"Task id not set, cannot update its progress to {current}%")


def list_tasks():
    """
    Returns list of all active and pending tasks
    """
    inspect = celery.control.inspect()

    active_tasks = [
        task for worker_tasks in inspect.active().values() for task in worker_tasks
    ]
    waiting_tasks = [
        task for worker_tasks in inspect.reserved().values() for task in worker_tasks
    ]
    return active_tasks + waiting_tasks


def find_task_id(task_name, args):
    """
    Returns a task id based on a task name and associated args
    """
    for task in list_tasks():
        if task["name"] == task_name and task["args"] == args:
            LOG.info(f"found a task with same context (name={task_name}, args={args})!")
            return task["id"]

    return None
