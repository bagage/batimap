#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from .city import City

from bs4 import BeautifulSoup
import http.cookiejar
import urllib.request
import zlib

LOG = logging.getLogger(__name__)


def stats(db, overpass, department=None, cities=[], force=False):
    if force:
        if department:
            update_departments_raster_state(db, department)
        else:
            depts = set([City(db, c).department for c in cities])
            update_departments_raster_state(db, depts)

    if department:
        cities = db.within_department(department)
    for city in cities:
        c = City(db, city)
        date = c.fetch_osm_data(overpass, force)
        yield((c, date))


def update_departments_raster_state(db, departments):
    url = 'https://www.cadastre.gouv.fr/scpc/rechercherPlan.do'
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = op.open(url)
    csrf_token = r.read().split(b'CSRF_TOKEN=')[1].split(b'"')[0].decode('utf-8')
    op.addheaders = [('Accept-Encoding', 'gzip')]

    for department in departments:
        LOG.info(f"Récupération des infos pour le département {department}")
        tuples = []
        department = f'{department}'
        r2 = op.open(f"https://www.cadastre.gouv.fr/scpc/listerCommune.do?CSRF_TOKEN={csrf_token}&" +
                     f"codeDepartement={department.zfill(3)}&libelle=&keepVolatileSession=&offset=5000")
        fr = BeautifulSoup(zlib.decompress(r2.read(), 16+zlib.MAX_WBITS), "lxml")

        for e in fr.find_all("tbody", attrs={"class": "parcelles"}):
            y = e.find(title="Ajouter au panier")
            if not y:
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

            name = db.name_for_insee(insee, True)
            if not name:
                LOG.critical(f"Cannot find city with insee {insee}, did you import OSM data for this department?")
                continue

            tuples.append((insee, dept, name, f"{code_commune}-{nom_commune}", is_raster))
        db.insert_stats_for_insee(tuples)


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
