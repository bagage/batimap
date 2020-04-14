#!/usr/bin/env python3
# This program is watching for Imposm database updates (eg OSM data changes)
# When update occurs, this script will refresh stats on data's cities
import requests
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from math import pi, degrees, atan, sinh
import time
import logging
import os
import threading

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
    level=verbosity[os.environ.get("IMPOSM_VERBOSITY") or config["DEFAULT"]["VERBOSITY"] or "CRITICAL"],
)
logging.getLogger("urllib3").setLevel(logging.WARNING)

BACK_URL = config["DEFAULT"]["BACK_URL"]
BACK_CITIES_IN_BBOX_URL = BACK_URL + "/bbox/cities"
BACK_INITDB_URL = BACK_URL + "/initdb"
BACK_TASKS_URL = BACK_URL + "/tasks/{task_id}"


class Watcher:
    DIRECTORY_TO_WATCH = "/data/"

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
    def convert_zxy_to_lonlat(z, x, y):
        n = pow(2, z)
        lon = x / n * 360.0 - 180.0
        lat = degrees(atan(sinh(pi * (1 - (2 * y / n)))))
        return [round(lon, 6), round(lat, 6)]

    @staticmethod
    def on_any_event(event):
        LOG.debug(f"New event: {event}, is_directory={event.is_directory}, event_type={event.event_type}")
        if event.is_directory:
            return

        if event.event_type in ["modified", "created"]:
            Handler.parse_entries(event.src_path)
        elif event.event_type == "moved":
            Handler.parse_entries(event.dest_path)

    @staticmethod
    def wait_task_completion(r):
        if r.status_code == 202:
            task_url = BACK_TASKS_URL.format(**r.json())
            LOG.info(f"You can follow the progress of initdb on {task_url}")
            Handler.get_task_status(task_url)
        else:
            LOG.warning(f"Error {r.status_code} {r.reason} while invoking initdb: {r.text}")

    @staticmethod
    def get_task_status(url):
        r = requests.get(url=url)
        content = r.json()
        state = content["state"]
        result = content["result"]

        if r.status_code != 200 or state in ["FAILURE", "SUCCESS"]:
            LOG.info(f"initdb terminated {state}: {result if result else '<empty response>'}")
        else:
            if state == "PROGRESS":
                LOG.debug(f"initdb progress: {result['current']}/{result['total']}")
            timer = threading.Timer(30, Handler.get_task_status, args=(url,))
            timer.daemon = True
            timer.start()

    @staticmethod
    def chunks(array, n):
        """Yield striped chunks from array of n items."""
        for i in range(0, len(array), n):
            yield array[i : i + n]

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

        bboxes = []
        for i, line in enumerate(lines):
            LOG.debug(f"entry {i+1} / {len(lines)}: {line.strip()}")
            # line is Z/X/Y format like '11/1058/702'
            z, x, y = map(int, line.split("/"))
            lonNW, latNW = Handler.convert_zxy_to_lonlat(z, x, y)
            lonSE, latSE = Handler.convert_zxy_to_lonlat(z, x + 1, y + 1)

            bboxes.append([lonNW, latNW, lonSE, latSE])

        cities = []

        LOG.debug(f"{BACK_CITIES_IN_BBOX_URL} - {bboxes}")
        # we cannot request too much at once because it timeouts..
        for chunk in Handler.chunks(bboxes, 100):
            r = requests.post(url=BACK_CITIES_IN_BBOX_URL, json={"bboxes": bboxes})
            cities += [c["insee"] for c in r.json()]
            LOG.debug(f"{r.text}")

        cities.sort()

        if len(cities):
            LOG.info(f"Running initdb on {cities}")
            Handler.wait_task_completion(requests.post(url=BACK_INITDB_URL, json={"cities": cities}))
        else:
            LOG.warning("No cities found in file!")


if __name__ == "__main__":
    w = Watcher()
    w.run()
