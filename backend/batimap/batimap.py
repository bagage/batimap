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
        (date, author) = c.fetch_osm_data(overpass, force)
        yield((c, date, author))


def generate(db, cities):
    for city in cities:
        c = City(db, city)
        city_path = c.get_work_path()
        if city_path and not path.exists(city_path):
            c.fetch_cadastre_data()
        else:
            LOG.debug("{} est déjà prêt".format(c))


def work(db, cities):
    for city in cities:
        c = City(db, city)
        LOG.debug("Récupération de la date du dernier import…")
        date = c.get_last_import_date()
        city_path = c.get_work_path()
        if date == str(datetime.datetime.now().year):
            need_work = False
            LOG.debug("{} déjà à jour".format(c))
        else:
            need_work = city_path is not None

        if need_work:
            if not path.exists(city_path):
                LOG.debug("Téléchargement des données depuis le cadastre…")
                if not c.fetch_cadastre_data():
                    LOG.error(
                        "Échec de téléchargement des données du cadastre.")
                    return

            LOG.debug("Configuration de JOSM…")
            if not Josm.do_work(c):
                return

        if path.exists(city_path):
            LOG.debug(
                "Déplacement de {} vers les archives".format(city_path))
            shutil.move(city_path, path.join(
                City.WORKDONE_PATH, path.basename(city_path)))
