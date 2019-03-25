#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from .city import City

from bs4 import BeautifulSoup, SoupStrainer
import http.cookiejar
import urllib.request
import zlib
import requests
import datetime
from contextlib import closing
import re
import json
from collections import Counter

LOG = logging.getLogger(__name__)
IGNORED_BUILDINGS = ["church"]
NO_BUILDING_CITIES = ["55139", "55039", "55307", "55050", "55239"]


def stats(db, overpass, department=None, cities=[], force=False, refresh_cadastre_state=False):
    if refresh_cadastre_state:
        if department:
            next(update_departments_raster_state(db, [department]))
        else:
            depts = set([City(db, c).department for c in cities])
            list(update_departments_raster_state(db, depts))

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
    for idx, d in enumerate(departments):
        LOG.info(f"Récupération des infos cadastrales pour le département {d}")
        if len(db.within_department(d)) > 0 and len(db.within_department_raster(d)) == 0:
            LOG.info(f"Le département {d} ne contient que des communes vectorisées, rien à faire")
            continue
        tuples = []
        d = f"{d}"
        r2 = op.open(
            f"https://www.cadastre.gouv.fr/scpc/listerCommune.do?CSRF_TOKEN={csrf_token}"
            f"&codeDepartement={d.zfill(3)}&libelle=&keepVolatileSession=&offset=5000"
        )
        cities = SoupStrainer("tbody", attrs={"class": "parcelles"})
        fr = BeautifulSoup(zlib.decompress(r2.read(), 16 + zlib.MAX_WBITS), "lxml", parse_only=cities)
        LOG.debug(f"Query result: {fr.prettify()}")
        for e in fr.find_all("tbody"):
            y = e.find(title="Ajouter au panier")
            if not y:
                continue

            # y.get('onclick') structure: "ajoutArticle('CL098','VECT','COMU');"
            (_, code_commune, _, format_type, _, _, _) = y.get("onclick").split("'")

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
        LOG.debug(f"Inserting {len(tuples)} cities in database…")
        db.insert_stats_for_insee(tuples)
        yield idx + 1


def fetch_departments_osm_state(db, departments):
    LOG.info(f"Récupération du statut OSM pour les départements {departments}")
    for idx, d in enumerate(departments):
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
                date = datetime.datetime.strptime(e.select("td:nth-of-type(3)")[0].text.strip(), "%d-%b-%Y %H:%M")

                tuples.append((name_cadastre, date))

                c = City(db, name_cadastre)
                if c.insee and c.date_cadastre != date:
                    LOG.debug(f"Cadastre changed changed for {c} from {c.date_cadastre} to {date}")
                    refresh_tiles.append(c.insee)

        db.upsert_city_status(tuples)
        for insee in refresh_tiles:
            clear_tiles(db, insee)
        yield idx + 1


def josm_data(db, insee, overpass):
    c = City(db, insee)
    if not c:
        return None

    base_url = f"https://cadastre.openstreetmap.fr/data/{c.department.zfill(3)}/{c.name_cadastre}-houses-"
    bbox = c.get_bbox()

    # force refreshing city latest import date
    (_, date) = fetch_osm_data(db, c, overpass, True)
    return {
        "buildingsUrl": base_url + "simplifie.osm",
        "segmententationPredictionssUrl": base_url + "prediction_segmente.osm",
        "bbox": [bbox.xmin, bbox.xmax, bbox.ymin, bbox.ymax],
        "date": date,
    }


def fetch_cadastre_data(city):
    __total_pdfs_regex = re.compile(r".*coupe la bbox en (\d+) \* (\d+) \[(\d+) pdfs\]$")
    __pdf_progression_regex = re.compile(r".*\d+-(\d+)-(\d+).pdf$")

    if not city or not city.name_cadastre:
        return

    # force refresh if cadastre data is too old
    force = city.date_cadastre is not None and not city.is_josm_ready()

    url = "https://cadastre.openstreetmap.fr"
    dept = city.department.zfill(3)
    r = requests.get(f"{url}/data/{dept}/")
    bs = BeautifulSoup(r.content, "lxml")

    if not force:
        archive = f"{city.name_cadastre.upper()}-houses-simplifie.osm"
        for e in bs.find_all("tr"):
            if archive in [x.text for x in e.select("td:nth-of-type(2) a")]:
                date = e.select("td:nth-of-type(3)")[0].text.strip()
                LOG.info(f"{city.name_cadastre} was already generated at {date}, no need to regenerate it!")
                return

    data = {"dep": dept, "type": "bati", "force": str(force).lower(), "ville": city.name_cadastre}

    # otherwise we invoke Cadastre generation
    with closing(requests.post(url, data=data, stream=True)) as r:
        (total_y, total) = (0, 0)
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
                yield current * 100 / total
            if "Termin" in line:
                current = total
                msg = f"{city} - {current}/{total} ({current * 100.0 / total:.2f}%)" if total > 0 else f"{current}"
                LOG.info(msg)
                yield 100
            elif "ERROR:" in line or "ERREUR:" in line:
                LOG.error(line)
                # may happen when cadastre.gouv.fr is in maintenance mode
                raise Exception(line)


def clear_tiles(db, insee):
    bbox = db.bbox_for_insee(insee)
    with open("tiles/outdated.txt", "a") as fd:
        fd.write(str(bbox) + "\n")


cadastre_src2date_regex = re.compile(r".*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*")


def fetch_osm_data(db, city, overpass, force):
    """
    Compute the latest import date for given city
    """
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
                  node['building'='church'](area.a);
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
            elements = response.get("elements")
            buildings = []
            has_simplified_buildings = False
            for element in elements:
                if element.get("type") == "node":
                    LOG.info(
                        f"{city} contient des bâtiments "
                        f"avec une géométrie simplifée {element}, import probablement jamais réalisé"
                    )
                    has_simplified_buildings = True

                tags = element.get("tags")
                buildings.append((tags.get("source") or "") + (tags.get("source:date") or ""))
            (date, sources_date) = date_for_buildings(city.insee, buildings, has_simplified_buildings)
        # only update date if we did not use cache files for buildings
        city.details = {"dates": sources_date}
        db.update_stats_for_insee([(city.insee, city.name, date, json.dumps(city.details))])
    return (city, date)


def date_for_buildings(insee, buildings, has_simplified_buildings):
    """
    Computes the city buildings import date, given a list of buildings with their indiviual import date
    """

    if insee in NO_BUILDING_CITIES:
        LOG.info(f"City {insee} is a no-buildings city. Assuming it was imported this year.")
        return (str(datetime.date.today().year), [])

    sources_date = []
    for b in buildings:
        source = (b or "unknown").lower()
        date = re.sub(cadastre_src2date_regex, r"\2", source)
        sources_date.append(date)
    counter = Counter(sources_date)
    LOG.debug(f"City {insee} stats: {counter}")

    date = max(counter, key=sources_date.count) if len(sources_date) else "never"
    if date != "never" and date != "raster":
        date_match = re.compile(r"^(\d{4})$").match(date)
        date = date_match.groups()[0] if date_match and date_match.groups() else "unknown"
        # If a city has a few buildings, and **even if a date could be computed**, we assume
        # it was never imported (sometime only 1 building on the boundary is wrongly computed)
        # Almost all cities have at least church/school/townhall manually mapped
        if len(buildings) < 10:
            LOG.info(f"City {insee}: few buildings found ({len(buildings)}), assuming it was never imported!")
            date = "never"
        elif has_simplified_buildings:
            date = "unfinished"
    return (date, counter)
