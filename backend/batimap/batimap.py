#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from .city import City

from bs4 import BeautifulSoup
import http.cookiejar
import urllib.request
import zlib
import requests
import datetime
from contextlib import closing
import re

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

            date = 'raster' if is_raster else None
            tuples.append((insee, dept, name, f"{code_commune}-{nom_commune}", is_raster, date))
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


def fetch_cadastre_data(city, force=False):
    __total_pdfs_regex = re.compile(
        ".*coupe la bbox en \d+ \* \d+ \[(\d+) pdfs\]$")

    if not city or not city.name_cadastre:
        return False

    url = 'https://cadastre.openstreetmap.fr'

    dept = city.department.zfill(3)

    r = requests.get(f"{url}/data/{dept}/")
    bs = BeautifulSoup(r.content, "lxml")

    for e in bs.find_all('tr'):
        if f"{city.name_cadastre.upper()}.tar.bz2" in [x.text for x in e.select('td:nth-of-type(2) a')]:
            date = e.select('td:nth-of-type(3)')[0].text.strip()
            if (datetime.datetime.now() - datetime.datetime.strptime(date, "%d-%b-%Y %H:%M")).days > 30:
                LOG.warn(f"{city.name_cadastre} was already generated at {date}, but is too old so refreshing it…")
                force = True
            else:
                LOG.info(f"{city.name_cadastre} was already generated at {date}, no need to regenerate it!")

    data = {
        'dep': dept,
        'type': 'bati',
        # fixme: if data is too old, we should ask for new generation
        'force': 'true' if force else 'false',
        'ville': city.name_cadastre,
    }

    # otherwise we invoke Cadastre generation
    with closing(requests.post(url, data=data, stream=True)) as r:
        total = 0
        current = 0
        for line in r.iter_lines(decode_unicode=True):
            # only display progression
            # TODO: improve this…
            if "coupe la bbox en" in line:
                match = __total_pdfs_regex.match(line)
                if match:
                    total = int(match.groups()[0])

            if line.endswith(".pdf"):
                current += 1
                msg = f"{current}/{total} ({current * 100.0 / total:.2f}%)" if total > 0 else f"{current}"
                LOG.info(msg)
            elif "ERROR:" in line or "ERREUR:" in line:
                LOG.error(line)
                return False
    return True
