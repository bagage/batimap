class TaskDTO:
    task_id = None
    name = None
    args = None
    running = None

    def __init__(self, task):
        self.task_id = task["id"]
        self.name = task["name"].split(".")[-1]
        self.args = task["args"]
        self.running = task["time_start"] is not None
