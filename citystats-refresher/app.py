#!/usr/bin/env python3

import requests
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

BACK_CITIES_IN_BBOX_URL = config["DEFAULT"]["BACK_URL"] + "/cities/in_bbox/{lonNW}/{latNW}/{lonSE}/{latSE}"
BACK_INITDB_URL = config["DEFAULT"]["BACK_URL"] + "/initdb"
BACK_TASKS_URL = config["DEFAULT"]["BACK_URL"] + "/tasks/{task_id}"


class Watcher:
    DIRECTORY_TO_WATCH = "/data/tiles"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        LOG.info(f"starting watch directory {self.DIRECTORY_TO_WATCH}")
        self.observer.start()
        try:
            while self.observer.is_alive():
                time.sleep(5)
        except Exception as e:
            LOG.error("Error " + str(e))
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        LOG.debug(f"New event: {event}, is_directory={event.is_directory}, event_type={event.event_type}")
        if event.is_directory:
            return None
        elif event.event_type == "modified":
            return Handler.parse_entries(event.src_path)
        elif event.event_type == "moved":
            return Handler.parse_entries(event.dest_path)

    @staticmethod
    def parse_entries(file_path):
        LOG.info(f"New entries in {file_path}")
        lines = []
        try:
            with open(file_path) as f:
                lines = f.readlines()
        except Exception as e:
            LOG.warning(f"Could not read entries in {file_path}: {e}")
            return None
        cities = []
        for i, line in enumerate(lines):
            LOG.debug(f"entry {i} / {len(lines)} : {line}")
            # each line is like: '4.39307577596182,48.7899945842883,4.4969189229214,48.8514051846223\n'
            (lonW, latS, lonE, latN) = line.strip().split(",")
            args = {"lonNW": lonW, "latNW": latN, "lonSE": lonE, "latSE": latS}
            LOG.debug(BACK_CITIES_IN_BBOX_URL.format(**args))
            r = requests.get(url=BACK_CITIES_IN_BBOX_URL.format(**args))
            cities += [x["insee"] for x in r.json()]
            LOG.debug(r.text)
        cities = sorted(list(set(cities)))
        if len(cities):
            LOG.info(f"Running initdb on {cities}")
            r = requests.post(url=BACK_INITDB_URL, json={"cities": cities})
            if r.status_code == 202:
                LOG.info(f"You can follow the progress of initdb on {BACK_TASKS_URL.format(**r.json())}")
            else:
                LOG.warning(f"Error {r.status_code} {r.reason} while invoking initdb: {r.text}")
        else:
            LOG.warning("No cities found in file!")


if __name__ == "__main__":
    w = Watcher()
    w.run()
