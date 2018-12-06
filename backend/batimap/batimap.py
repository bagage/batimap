#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from .city import City

from bs4 import BeautifulSoup
import http.cookiejar
import urllib.request
import zlib
import requests
from datetime import datetime
from contextlib import closing
import re
import json
from collections import Counter

LOG = logging.getLogger(__name__)
IGNORED_BUILDINGS = ["church"]


def stats(db, overpass, department=None, cities=[], force=False, refresh_cadastre_state=False):
    if refresh_cadastre_state:
        if department:
            update_departments_raster_state(db, [department])
        else:
            depts = set([City(db, c).department for c in cities])
            update_departments_raster_state(db, depts)

    if department:
        cities = db.within_department(department)
    for city in cities:
        c = City(db, city)
        yield fetch_osm_data(db, c, overpass, force)


def update_departments_raster_state(db, departments):
    url = "https://www.cadastre.gouv.fr/scpc/rechercherPlan.do"
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = op.open(url)
    csrf_token = r.read().split(b"CSRF_TOKEN=")[1].split(b'"')[0].decode("utf-8")
    op.addheaders = [("Accept-Encoding", "gzip")]

    LOG.info(f"Récupération des infos cadastrales pour les départements {departments}")
    for d in departments:
        LOG.info(f"Récupération des infos cadastrales pour le département {d}")
        tuples = []
        d = f"{d}"
        r2 = op.open(
            f"https://www.cadastre.gouv.fr/scpc/listerCommune.do?CSRF_TOKEN={csrf_token}"
            f"&codeDepartement={d.zfill(3)}&libelle=&keepVolatileSession=&offset=5000"
        )
        fr = BeautifulSoup(zlib.decompress(r2.read(), 16 + zlib.MAX_WBITS), "lxml")
        for e in fr.find_all("tbody", attrs={"class": "parcelles"}):
            y = e.find(title="Ajouter au panier")
            if not y:
                continue

            # y.get('onclick') structure: "ajoutArticle('CL098','VECT','COMU');"
            split = y.get("onclick").split("'")
            code_commune = split[1]
            format_type = split[3]

            # e.strong.string structure: "COBONNE (26400) "
            commune_cp = e.strong.string
            nom_commune = commune_cp[:-9]

            dept = d.zfill(2)
            start = len(dept) - 5
            insee = dept + code_commune[start:]
            is_raster = format_type == "IMAG"

            name = db.name_for_insee(insee)
            if not name:
                LOG.error(f"Cannot find city with insee {insee}, did you import OSM data for this department?")
                continue

            date = "raster" if is_raster else "never"
            tuples.append((insee, dept, name, f"{code_commune}-{nom_commune}", is_raster, date))
        db.insert_stats_for_insee(tuples)


def fetch_departments_osm_state(db, departments):
    LOG.info(f"Récupération du statut OSM pour les départements {departments}")
    for d in departments:
        LOG.info(f"Récupération du statut OSM pour le département {d}")
        tuples = []
        url = "https://cadastre.openstreetmap.fr"
        dept = d.zfill(3)
        r = requests.get(f"{url}/data/{dept}/")
        bs = BeautifulSoup(r.content, "lxml")
        refresh_tiles = []
        for e in bs.select("tr"):
            osm_data = e.select("td > a")
            if len(osm_data):
                osm_data = osm_data[0].text
                if not osm_data.endswith("simplifie.osm") or "-extrait-" in osm_data:
                    continue
                name_cadastre = "-".join(osm_data.split("-")[:-2])
                date = datetime.strptime(e.select("td:nth-of-type(3)")[0].text.strip(), "%d-%b-%Y %H:%M")

                tuples.append((name_cadastre, date))

                c = City(db, name_cadastre)
                if c.insee and c.date_cadastre != date:
                    LOG.debug(f"Cadastre changed changed for {c} from {c.date_cadastre} to {date}")
                    refresh_tiles.append(c.insee)

        db.upsert_city_status(tuples)
        for insee in refresh_tiles:
            clear_tiles(db, insee)


def josm_data(db, insee):
    c = City(db, insee)
    if not c:
        return None

    base_url = f"https://cadastre.openstreetmap.fr/data/{c.department.zfill(3)}/{c.name_cadastre}-houses-"
    bbox = c.get_bbox()

    return {
        "buildingsUrl": base_url + "simplifie.osm",
        "segmententationPredictionssUrl": base_url + "prediction_segmente.osm",
        "bbox": [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax],
    }


def fetch_cadastre_data(city, force=False):
    __total_pdfs_regex = re.compile(r".*coupe la bbox en (\d+) \* (\d+) \[(\d+) pdfs\]$")
    __pdf_progression_regex = re.compile(r".*\d+-(\d+)-(\d+).pdf$")

    if not city or not city.name_cadastre:
        return False

    url = "https://cadastre.openstreetmap.fr"
    dept = city.department.zfill(3)
    r = requests.get(f"{url}/data/{dept}/")
    bs = BeautifulSoup(r.content, "lxml")

    for e in bs.find_all("tr"):
        if f"{city.name_cadastre.upper()}.tar.bz2" in [x.text for x in e.select("td:nth-of-type(2) a")]:
            date = e.select("td:nth-of-type(3)")[0].text.strip()
            LOG.info(f"{city.name_cadastre} was already generated at {date}, no need to regenerate it!")
            return True

    data = {
        "dep": dept,
        "type": "bati",
        # fixme: if data is too old, we should ask for new generation
        "force": "true" if force else "false",
        "ville": city.name_cadastre,
    }

    # otherwise we invoke Cadastre generation
    with closing(requests.post(url, data=data, stream=True)) as r:
        (total_y, total) = (0, 0)
        current = 0
        for line in r.iter_lines(decode_unicode=True):
            match = __total_pdfs_regex.match(line)
            if match:
                total_y = int(match.groups()[1])
                total = int(match.groups()[2])
            match = __pdf_progression_regex.match(line)
            if match:
                x = int(match.groups()[0])
                y = int(match.groups()[1])
                current = x * total_y + y
                msg = f"{city} - {current}/{total} ({current * 100.0 / total:.2f}%)" if total > 0 else f"{current}"
                LOG.info(msg)
            if "Termin" in line:
                current = total
                msg = f"{city} - {current}/{total} ({current * 100.0 / total:.2f}%)" if total > 0 else f"{current}"
                LOG.info(msg)
            elif "ERROR:" in line or "ERREUR:" in line:
                LOG.error(line)
                return False

    return True


def clear_tiles(db, insee):
    bbox = db.bbox_for_insee(insee)
    with open("tiles/outdated.txt", "a") as fd:
        fd.write(str(bbox) + "\n")


cadastre_src2date_regex = re.compile(r".*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*")


def fetch_osm_data(db, city, overpass, force):
    date = city.get_last_import_date()
    if force or date is None:
        sources_date = []
        if city.is_raster:
            date = "raster"
        else:
            ignored_buildings = "".join(['[building!="' + x + '"]' for x in IGNORED_BUILDINGS])
            request = f"""[out:json];
                area[boundary='administrative'][admin_level~'8|9']['ref:INSEE'='{city.insee}']->.a;
                (
                  way['building']{ignored_buildings}(area.a);
                  relation['building']{ignored_buildings}(area.a);
                );
                out tags qt meta;"""
            try:
                response = overpass.request_with_retries(request)
            except Exception as e:
                LOG.error(f"Failed to count buildings for {city}: {e}")
                return (None, None)
            # iterate on every building
            buildings = response.get("elements")
            for element in buildings:
                tags = element.get("tags")
                source = (tags.get("source") or "unknown").lower()
                source_date = (tags.get("source:date") or "").lower()
                date = re.sub(cadastre_src2date_regex, r"\2", source + source_date)
                sources_date.append(date)

            date = max(sources_date, key=sources_date.count) if len(sources_date) else "never"
            if date != "never":
                date_match = re.compile(r"^(\d{4})$").match(date)
                date = date_match.groups()[0] if date_match and date_match.groups() else "unknown"
                # assume that low number of buildings with no date is just no import:
                # only church/school/townhall may have been manually created
                if date == "unknown" and len(buildings) < 10:
                    date = "never"

            LOG.debug(f"City stats: {Counter(sources_date)}")
        # only update date if we did not use cache files for buildings
        city.details = {"dates": Counter(sources_date)}
        db.update_stats_for_insee([(city.insee, city.name, date, json.dumps(city.details), True)])
    return (city, date)
