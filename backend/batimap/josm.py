import logging
import os
import subprocess
import time
from collections import OrderedDict
from os import path

import requests

LOG = logging.getLogger(__name__)


class Josm(object):
    base_url = 'http://0.0.0.0:8111/'

    def get_executable_path(self):
        for p in os.environ['PATH']:
            if p.lower().endswith("josm"):
                return p

        for d in [
                os.environ['HOME'] + "/.local/share/applications/",
                "/usr/share/applications",
                "/usr/local/share/applications"
        ]:
            desktop = path.join(d, "josm.desktop")
            if os.path.exists(desktop):
                with open(desktop, 'r') as fd:
                    for line in fd:
                        if "Exec=" in line:
                            # could probably be better
                            cmd = "=".join(line.split("=")[1:]).split(" ")
                            cmd = [x for x in cmd if not x.startswith("%")]
                            return cmd

        return None

    def is_started(self):
        try:
            r = requests.get(self.base_url + 'version')
            return r.status_code == 200
        except Exception:
            return False

    def start(self):
        # Hack: look in PATH and .desktop files if JOSM is referenced
        josm_path = self.get_executable_path()
        # If we found it, start it and try to connect to it (aborting after 1
        # min)
        if josm_path:
            stdouterr = None if LOG.getEffectiveLevel(
            ) == logging.DEBUG else subprocess.PIPE
            subprocess.Popen(josm_path, stdout=stdouterr, stderr=stdouterr)
            timeout = time.time() + 60
            while True:
                if self.is_started() or time.time() > timeout:
                    return True
                elif time.time() > timeout:
                    LOG.critical(
                        "Impossible de se connecter à JOSM - est-il lancé ?")
                time.sleep(1)
        return False

    def do_work(self, city):

        # a. ensure JOSM is running
        try:
            r = requests.get(self.base_url + 'version')
        except Exception:
            LOG.info("JOSM ne semble pas démarré, en attente de lancement…")
            self.start()

        # b. open Strava and BDOrtho IGN imageries
        imageries = OrderedDict([
            ("BDOrtho IGN",
             "url=http://proxy-ign.openstreetmap.fr/bdortho/{zoom}/{x}/{y}.jpg")
        ])
        for k, v in imageries.items():
            r = requests.get(
                self.base_url + 'imagery?title={}&type=tms&{}'.format(k, v))

        # c. open both houses-simplifie.osm and houses-prediction_segmente.osm
        # files
        city_path = city.get_work_path()
        files = [path.join(city_path, x) for x in os.listdir(city_path)
                 if x.endswith('-houses-simplifie.osm') or x.endswith('-houses-prediction_segmente.osm')]
        files.sort()
        for x in files:
            r = requests.get(self.base_url + 'open_file?filename={}'.format(x))
            if r.status_code != 200:
                error = r.text
                if r.status_code == 403:
                    error = "did you enable 'Open local files' in Remote Control Preferences?"

                LOG.critical("Impossible de lancer JOSM ({}): {}".format(
                    r.status_code, error))
                break

        # d. download city data from OSM as well
        bbox = city.get_bbox()
        url = \
            self.base_url + \
            'load_and_zoom?new_layer=true&layer_name=Données OSM pour {} - {}&left={}&right={}&bottom={}&top={}'
        url = url.format(city.insee, city.name,
                         bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax)
        r = requests.get(url)
        if r.status_code != 200:
            LOG.critical("Impossible de charger les données OSM ({}): {}".format(
                r.status_code, r.text))

        while self.is_started():
            time.sleep(5)
        return True
