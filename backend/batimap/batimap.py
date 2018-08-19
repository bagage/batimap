#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import logging
import shutil
from os import path

from .city import City
from .josm import Josm

from bs4 import BeautifulSoup
import http.cookiejar
import urllib.request

LOG = logging.getLogger(__name__)


def stats(db, overpass, department=None, cities=[], force=False):
    if force:
        if department:
            update_department_raster_state(db, department)
        else:
            depts = set([City(db, c).department for c in cities])
            for d in depts:
                update_department_raster_state(db, d)

    if department:
        cities = db.within_department(department)

    for city in cities:
        c = City(db, city)
        date = c.fetch_osm_data(overpass, force)
        yield((c, date))


def generate(db, cities):
    for city in cities:
        c = City(db, city)
        city_path = c.get_work_path()
        if city_path and not path.exists(city_path):
            c.fetch_cadastre_data()
        else:
            LOG.debug("{} est déjà prêt".format(c))


def update_department_raster_state(db, department):
    url = 'https://www.cadastre.gouv.fr/scpc/rechercherPlan.do'
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = op.open(url)
    csrf_token = r.read().split(b'CSRF_TOKEN=')[1].split(b'"')[0].decode('utf-8')

    LOG.debug(f"Récupération des infos pour le département {department}")
    department = f'{department}'
    r2 = op.open(f"https://www.cadastre.gouv.fr/scpc/listerCommune.do?CSRF_TOKEN={csrf_token}&codeDepartement={department.zfill(3)}&libelle=&keepVolatileSession=&offset=5000")

    fr = BeautifulSoup(r2.read(), "lxml")
    for e in fr.find_all(attrs={"class": "parcelles"}):
        y = e.find(title="Ajouter au panier")
        if y is None:
            continue

        # y.get('onclick') structure: "ajoutArticle('CL098','VECT','COMU');"
        split = y.get('onclick').split("'")
        code_commune = split[1]
        format_type = split[3]

        # e.strong.string structure: "COBONNE (26400) "
        commune_cp = e.strong.string
        nom_commune = commune_cp[:-9]

        dept = department.zfill(2)
        insee = dept + code_commune[-3:]
        is_raster = format_type == 'IMAG'
        db.insert_stats_for_insee(insee, dept, f"{code_commune}-{nom_commune}", is_raster)


def work(db, cities, force=False):
    for city in cities:
        c = City(db, city)
        LOG.debug("Récupération de la date du dernier import…")
        date = c.get_last_import_date()
        city_path = c.get_work_path()
        need_work = False
        if not c.is_vectorized:
            LOG.error("{} n'est pas vectorisée !".format(c))
        elif date == str(datetime.datetime.now().year):
            LOG.debug("{} déjà à jour".format(c))
        else:
            need_work = city_path is not None
        if need_work:
            if force or not path.exists(city_path):
                LOG.debug("Téléchargement des données depuis le cadastre…")
                if not c.fetch_cadastre_data(force=force):
                    LOG.error(
                        "Échec de téléchargement des données du cadastre.")
                    return

            LOG.debug("Configuration de JOSM…")
            if not Josm().do_work(c):
                return

        if path.exists(city_path):
            LOG.debug(
                "Déplacement de {} vers les archives".format(city_path))
            shutil.move(city_path, path.join(
                City.WORKDONE_PATH, path.basename(city_path)))


def josm_data(db, insee):
    c = City(db, insee)
    if not c:
        return None

    base_url = f"https://cadastre.openstreetmap.fr/data/{c.department.zfill(3)}/{c.name_cadastre}-houses-"
    bbox = c.get_bbox()

    return {
        'buildingsUrl': base_url + "simplifie.osm",
        'segmententationPredictionssUrl': base_url + "prediction_segmente.osm",
        'bbox': [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax]
    }
