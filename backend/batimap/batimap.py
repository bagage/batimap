#!/usr/bin/env python3
import datetime
import logging
import shutil
from os import path

from .city import City
from .josm import Josm


LOG = logging.getLogger(__name__)


def stats(db, overpass, department=None, cities=[], force=False):
    if department:
        cities = db.within_department(department)

    for city in cities:
        c = City(db, city)
        c.fetch_osm_data(overpass, force)


def generate(db, cities):
    for city in cities:
        c = City(db, city)
        city_path = c.get_work_path()
        if city_path and not path.exists(city_path):
            c.fetch_cadastre_data()


def work(db, cities):
    for city in cities:
        c = City(db, city)
        date = c.get_last_import_date()
        city_path = c.get_work_path()
        if date == str(datetime.datetime.now().year):
            need_work = input(
                "{} déjà à jour, continuer quand même ? (oui/Non) ".format(c)).lower() == "oui"
        else:
            need_work = city_path is not None

        if need_work:
            if not path.exists(city_path):
                c.fetch_cadastre_data()

            if not Josm.do_work(c):
                return

        if path.exists(city_path):
            LOG.debug(
                "Déplacement de {} vers les archives".format(city_path))
            shutil.move(city_path, path.join(
                City.WORKDONE_PATH, path.basename(city_path)))
