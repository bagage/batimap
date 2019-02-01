#!/usr/bin/env python3

import requests
from math import degrees, sinh, atan, pi
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import time
import logging
import os

config = configparser.ConfigParser()
config.read("app.conf")

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
    level=verbosity[os.environ.get("INITDB_VERBOSITY") or config["DEFAULT"]["VERBOSITY"] or "CRITICAL"],
)

BACKEND_DEPARTMENTS_IN_BBOX_URL = (
    config["DEFAULT"]["BACKEND_URL"] + "/departments/in_bbox/{lonNW}/{latNW}/{lonSE}/{latSE}"
)
BACKEND_INITDB_URL = config["DEFAULT"]["BACKEND_URL"] + "/initdb?{}"
BACKEND_TASKS_URL = config["DEFAULT"]["BACKEND_URL"] + "/tasks/{task_id}"


def convert_zxy_to_lonlat(z, x, y):
    n = pow(2, z)
    lat = x / n * 360.0 - 180.0
    lon = degrees(atan(sinh(pi * (1 - (2 * y / n)))))
    return [lon, lat]


class Watcher:
    DIRECTORY_TO_WATCH = "/tiles"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        LOG.info(f"starting watch directory {self.DIRECTORY_TO_WATCH}")
        self.observer.start()
        try:
            while True:
                time.sleep(60)
        except Exception as e:
            LOG.error("Error " + str(e))
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == "modified":
            LOG.debug(f"New entries in {event.src_path}")
            lines = None
            with open(event.src_path) as f:
                lines = f.readlines()
            departments = []
            for i, line in enumerate(lines):
                LOG.debug(f"entry {i} / {len(lines)} : {line}")
                z, x, y = map(int, line.split("/"))
                lonNW, latNW = convert_zxy_to_lonlat(z, x, y)
                lonSE, latSE = convert_zxy_to_lonlat(z, x + 1, y + 1)
                args = {"lonNW": lonNW, "latNW": latNW, "lonSE": lonSE, "latSE": latSE}
                LOG.debug(BACKEND_DEPARTMENTS_IN_BBOX_URL.format(**args))
                r = requests.get(url=BACKEND_DEPARTMENTS_IN_BBOX_URL.format(**args))
                departments += r.json()
                LOG.debug(r.text)
            departments = sorted(list(set(departments)))
            LOG.info(f"Running initdb on {departments}")
            r = requests.post(url=BACKEND_INITDB_URL.format("&".join(departments)))
            LOG.debug(f"You can follow the progress of initdb on {BACKEND_TASKS_URL.format(**r.json())}")


if __name__ == "__main__":
    w = Watcher()
    w.run()
