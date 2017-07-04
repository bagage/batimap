#!/usr/bin/env python3

import argparse
from datetime import datetime
import json
import logging
import os
import re
import sys
import time
from collections import OrderedDict

from contextlib import closing
from os import path

from colorlog import ColoredFormatter

from colour import Color

import csv

import geojson
from geojson import Feature, FeatureCollection, Polygon

import overpass

import pygeoj

import requests

import psycopg2
import copy
import tarfile
import subprocess
import shutil

import math

BASE_PATH = path.normpath(
    path.join(path.dirname(path.realpath(__file__)), '..', 'data'))
WORKDONE_PATH = path.join(BASE_PATH, '_done')
WORKDONETAR_PATH = path.join(WORKDONE_PATH, 'tars')
STATS_PATH = path.join(BASE_PATH, 'stats')
DATA_PATH = path.join(STATS_PATH, 'cities')
os.makedirs(WORKDONE_PATH, exist_ok=True)
os.makedirs(WORKDONETAR_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(STATS_PATH, exist_ok=True)

log = None
API = None

CADASTRE_PROG = re.compile(r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')


def init_colors():
    # Retrieve the last cadastre import for the given insee municipality.
    # 2009 and below should be red,
    # current year should be green
    # previous year should be orange
    # below 2009 and previous year, use a color gradient
    this_year = datetime.now().year
    colors = list(Color('red').range_to(Color('orange'), this_year - 2009))
    colors.append(Color('green'))
    return dict(zip(range(2009, this_year + 1), [c.hex for c in colors]))


COLORS = init_colors()


def pseudo_distance(p1, p2):
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2


def overpass_request_with_retries(request, output_format='json'):
    for retry in range(9, 0, -1):
        try:
            response = API.Get(
                request, responseformat=output_format, build=False)
            return response
        except (overpass.errors.MultipleRequestsError, overpass.errors.ServerLoadError) as e:
            log.warning("{} occurred. Will retry again {} times in a few seconds".format(
                type(e).__name__, retry))
            if retry == 0:
                raise e
            # Sleep for n * 5 seconds before a new attempt
            time.sleep(5 * round((10 - retry) / 3))
    return None


def ringArea(coords):
    """
        This is borrowed from mapbox/geojson-rewind

        Calculate the approximate area of the polygon were it projected onto
          the earth.  Note that this area will be positive if ring is oriented
          clockwise, otherwise it will be negative.

        Reference:
        Robert. G. Chamberlain and William H. Duquette, "Some Algorithms for
          Polygons on a Sphere", JPL Publication 07-03, Jet Propulsion
          Laboratory, Pasadena, CA, June 2007 http://trs-new.jpl.nasa.gov/dspace/handle/2014/40409

        Returns:
        {float} The approximate signed geodesic area of the polygon in square
          meters.
    """
    area = 0

    if len(coords) > 2:
        for i in range(len(coords)-1):
            p1 = coords[i]
            p2 = coords[i + 1]
            area += math.radians(p2[0] - p1[0]) * (2 + math.sin(
                math.radians(p1[1])) + math.sin(math.radians(p2[1])))

        radius = 6378137
        area = area * radius * radius / 2

    return area


def correctRings(rings):
    """
    Polygons should be rotating anticlockwise (right-hand rule)
    """
    if ringArea(rings[0]) > 0:
        rings[0].reverse()
    for i in range(len(rings)):
        if ringArea(rings[i]) < 0:
            rings[i].reverse()
    return rings


def lines_to_polygons(ways):
    """
    Note: there might be multiple polygons for a single set of ways
    """

    if not ways:
        return []

    polygons = []
    border = ways.pop(0)
    while ways:
        dist = -1
        closest = 0
        reverse = False
        for i in range(len(ways)):
            d = pseudo_distance(border[-1], ways[i][0])
            if i == 0 or d < dist:
                dist = d
                closest = i
                reverse = False
            d = pseudo_distance(border[-1], ways[i][-1])
            if d < dist:
                dist = d
                closest = i
                reverse = True
        n = ways.pop(closest)
        if reverse:
            n.reverse()

        if dist == 0:
            n.pop(0)
            border += n
        else:
            polygons.append(border)
            border = n

    polygons.append(border)

    polygons = correctRings(polygons)
    return polygons


def color_by_date(date):
    try:
        date = int(date)
    except:
        if date:
            if date != "unknown":
                log.warning('Unknown date "{}"! Using gray.'.format(date))
            return 'gray'
        else:
            log.warning('No buildings found! Using pink.')
            return 'pink'

    if date <= 2009:
        return '#f00'
    else:
        return COLORS[date]


def department_for(insee):
    # Format of INSEE is [0-9]{2}[0-9]{3} OR 97[0-9]{1}[0-9]{2} for overseas
    # the first part is the department number, the second the city
    # unique id
    if insee.startswith('97'):
        return insee[:-2]
    else:
        return insee[:-3]


def stats_to_txt(stats):
    out = ''
    dates = sorted(stats.items(), key=lambda t: t[1])
    dates.reverse()
    total = sum(stats.values())
    for date, val in dates:
        out += '{}\t{} ({:.1%})\n'.format(date, val, val / total)
    out += 'Total\t{}\n'.format(total)
    return out


def get_municipality_relations(department, insee=None, force_download=False):
    log.info('Fetch cities boundary for department {} (via {})'.format(
        department, API.endpoint))

    json_path = path.join(STATS_PATH, '{}-limits.json'.format(department))

    if not force_download and path.exists(json_path):
        with open(json_path) as fd:
            result = json.load(fd)
        if insee:
            result = [x for x in result if x.get(
                'tags').get('ref:INSEE') == insee]

        # sometimes, the geometry of some cities is not set (probably due to an overpass error)
        # in that case, we will requery overpass instead
        for x in result:
            found = False
            for y in x.get('members'):
                if y.get('type') == 'way' and not y.get('role'):
                    log.error(
                        "Missing role for {} - requerying Overpass".format(x.get('tags').get('name')))
                    result = None
                    found = True
                    break
            if found:
                break

        if result:
            log.debug('Use cache file {}'.format(json_path))
            return result

    request = """[out:json];
        relation
          [boundary="administrative"]
          [admin_level=8]
          ["ref:INSEE"~"^{}"];
        out geom qt;""".format(insee if insee else department)

    response = overpass_request_with_retries(request)

    relations = response.get('elements')
    relations.sort(key=lambda x: x.get('tags').get('ref:INSEE'))

    if not insee:
        log.debug('Write cache file {}'.format(json_path))
        with open(json_path, 'w') as fd:
            fd.write(json.dumps(relations))

    return relations


def get_geometry_for(relation):
    outer_ways = []
    for member in relation.get('members'):
        if member.get('role') == 'outer':
            way = []
            for point in member.get('geometry'):
                way.append((point.get('lon'), point.get('lat')))
            outer_ways.append(way)
    borders = lines_to_polygons(outer_ways)

    if not borders:
        log.warning('{} does not have borders'.format(
            relation.get('tags').get('name')))
        exit(1)
        return None
    else:
        return Polygon(borders)


def build_municipality_list(department, vectorized, given_insee=None, force_download=None, umap=False, database=None):
    """Build municipality list
    """
    department = department.zfill(2)

    txt_content = ''
    department_stats = []
    connection = None

    if database:
        (host, port, user, password, database) = database.split(":")
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, database=database)
        cursor = connection.cursor()

    counter = 0
    relations = get_municipality_relations(
        department, given_insee, force_download == "all")
    for relation in relations:
        counter += 1

        tags = relation.get('tags')
        insee = tags.get('ref:INSEE')
        name = tags.get('name')
        postcode = tags.get('addr:postcode')

        if insee in vectorized:
            vector = 'vector'
            try:
                relation_src = count_sources(
                    'relation', insee, force_download in ["all", "relations"])['sources']
                building_src = count_sources(
                    'building', insee, force_download in ["all", "buildings"])['sources']
            except overpass.errors.ServerRuntimeError as e:
                log.error(
                    "Fail to query overpass for {}. Consider reporting the bug: {}. Skipping".format(insee, e))
                continue

            dates = sorted(building_src.items(),
                           key=lambda t: t[1], reverse=True)
            date = dates[0][0] if len(dates) else None
            color = color_by_date(date)
            description = 'Building:\n{}\nRelation:\n{}'.format(
                stats_to_txt(building_src), stats_to_txt(relation_src))
        else:
            date = 'raster'
            vector = 'raster'
            color = 'black'
            description = 'Raster'

        municipality_border = Feature(
            properties={
                'insee': insee,
                'name': name,
                'postcode': postcode,
                'description': description,
            },
        )

        if umap:
            municipality_border.properties['_storage_options'] = {
                'color': color,
                'weight': '1',
                'fillOpacity': '0.5',
                'labelHover': True,
            }
        else:
            municipality_border.properties['color'] = color

        municipality_border.geometry = get_geometry_for(relation)

        if database:
            log.debug("Updating database")
            try:
                req = ("""
                    INSERT INTO color_city
                    VALUES ('{}', '{}', '{}', now())
                    ON CONFLICT (insee) DO UPDATE SET color = excluded.color, department = excluded.department
                    """.format(insee, color, department))
                # only update date if we did not use cache files for buildings
                if force_download in ["all", "buildings"]:
                    req += ", last_update = excluded.last_update"
                cursor.execute(req)
            except Exception as e:
                log.warning("Cannot write in database: " + str(e))
                pass

        log.info("{:.2f}% Treated {} - {} (last import: {})".format(100 *
                                                                    counter / len(relations), insee, name, date))

        department_stats.append(municipality_border)
        txt_content += '{},{},{},{}\n'.format(insee, name, postcode, vector)

    if connection:
        # commit database changes only after the whole loop to 1. speed up 2. avoid
        # semi-updated database in case of error in the middle
        connection.commit()

    # write geojson
    log.debug('Write {}.geojson'.format(department))
    geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    if path.exists(geojson_path) and given_insee:
        department_geojson = geojson.loads(open(geojson_path).read())
        found = False
        for municipality in department_geojson["features"]:
            if municipality["properties"]["insee"] == given_insee:
                found = True
                index = department_geojson["features"].index(municipality)
                department_geojson["features"] = department_geojson["features"][
                    :index] + department_stats + department_geojson["features"][index + 1:]
                break
        if not found:
            department_geojson["features"] += department_stats

    else:
        department_geojson = FeatureCollection(department_stats)

    with open(geojson_path, 'w') as fd:
        # we should not indent the GeoJSON because it drastically reduce the final size
        # (x10 or so)
        fd.write(geojson.dumps(department_geojson, indent=None, sort_keys=True))

    # write txt
    log.debug('Write {}-municipality.txt'.format(department))
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


def get_bbox_for(insee):
    """
    Returns left/right/bottom/top (min and max latitude / longitude) of the
    bounding box around the INSEE code
    """
    relation = get_municipality_relations(department_for(insee), insee, False)
    city = pygeoj.new()
    city.add_feature(geometry=get_geometry_for(relation[0]))
    city.update_bbox()
    return city.bbox


def get_insee_for(name):
    log.info("Fetch INSEE for {}".format(name))

    csv_path = path.join(STATS_PATH, 'france-cities.csv')
    if not path.exists(csv_path):
        request = """
            area[boundary='administrative'][admin_level='2']['name'='France']->.a;
            relation[boundary="administrative"][admin_level=8](area.a)
        """

        response = overpass_request_with_retries(
            request, responseformat='csv("ref:INSEE","name")')
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in response.split("\n"):
                csv_writer.writerow(row.split("\t"))

    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        insee = [x['ref:INSEE']
                 for x in csv_reader if x['name'].startswith(name)]
        if len(insee) == 0:
            log.critical("Cannot found city with name {}.".format(name))
            exit(1)
        elif len(insee) == 1:
            return insee[0]
        elif len(insee) > 30:
            log.critical(
                "Too many cities with name {} (total: {}). Please check name.".format(name, len(insee)))
            exit(1)
        else:
            user_input = ""
            while user_input not in insee:
                user_input = input(
                    "More than one city found. Please enter your desired one from the following list:\n\t{}\n".format('\n\t'.join(insee)))
            return user_input


def get_vectorized_insee(department):
    department = department.zfill(2)
    log.info('Fetch list of vectorized cities in department {}'.format(department))
    json_path = path.join(STATS_PATH, '{}-cadastre.json'.format(department))

    if path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            return json.load(fd)

    vectorized = []
    response = requests.get(
        'http://cadastre.openstreetmap.fr/data/{0}/{0}-liste.txt'.format(department.zfill(3)))
    if response.status_code >= 400:
        log.critical('Unknown department {}'.format(department))
        exit(1)

    for _, code, _ in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
        if department.startswith('97'):
            vectorized.append('{}{}'.format(department, code[3:]))
        else:
            vectorized.append('{}{}'.format(department, code[2:]))

    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(vectorized, indent=4))

    return vectorized


def count_sources(datatype, insee, force_download):
    log.debug('Count {} sources for {} (via {})'.format(
        datatype, insee, API.endpoint))

    json_path = path.join(DATA_PATH, '{}.{}.json'.format(insee, datatype))
    if not force_download and path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            content = json.load(fd)
            if 'sources' in content and 'authors' in content:
                return content

    if datatype == 'building':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( node['building'](area.a);
              way['building'](area.a);
              relation['building'](area.a);
            );
            out tags qt meta;""".format(insee)
    elif datatype == 'relation':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( way['building'](area.a);
              node(w)['addr:housenumber'];
            );
            out tags qt;""".format(insee)

    for retry in range(9, 0, -1):
        try:
            response = overpass_request_with_retries(request)
            break
        except (overpass.errors.MultipleRequestsError, overpass.errors.ServerLoadError) as e:
            log.warning("{} occurred. Will retry again {} times in a few seconds".format(
                type(e).__name__, retry))
            if retry == 0:
                raise e
            # Sleep for n * 5 seconds before a new attempt
            time.sleep(5 * round((10 - retry) / 3))

    sources = {}
    authors = {}
    for element in response.get('elements'):
        src = element.get('tags').get('source') or 'unknown'
        src = src.lower()
        src = re.sub(CADASTRE_PROG, r'\2', src)
        sources[src] = sources[src] + 1 if src in sources else 1

        author = element.get('user') or 'unknown'
        authors[author] = authors[author] + 1 if author in authors else 1
    content = {}
    content['sources'] = sources
    content['authors'] = authors
    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(content, sort_keys=True, indent=4))

    return content


def get_josm_path():
    for p in os.environ['PATH']:
        if p.lower().endswith("josm"):
            return p

    for d in [os.environ['HOME'] + "/.local/share/applications/", "/usr/share/applications", "/usr/local/share/applications"]:
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


def start_josm(base_url):
        # Hack: look in PATH and .desktop files if JOSM is referenced
    josm_path = get_josm_path()
    # If we found it, start it and try to connect to it (aborting after 1
    # min)
    if josm_path:
        subprocess.Popen(josm_path)
        timeout = time.time() + 60
        while True:
            try:
                r = requests.get(base_url + 'version')
                if r.status_code == 200 or time.time() > timeout:
                    return True
            except:
                pass
        if time.time() > timeout:
            log.critical(
                "Cannot connect to JOSM - is it running? Tip: add JOSM to your PATH so that I can run it for you ;)")
    return False


def init_overpass(args):
    endpoints = {
        'overpass.de': 'https://overpass-api.de/api/interpreter',
        'api.openstreetmap.fr': 'http://api.openstreetmap.fr/oapi/interpreter',
        # default port/url for docker image
        'localhost': 'http://localhost:5001/api/interpreter'
    }
    global API

    API = overpass.API(endpoint=endpoints[args.overpass], timeout=300)


def init_log(args):
    levels = {
        'no': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }
    global log
    log_level = levels[args.verbose]
    logging.root.setLevel(log_level)
    if sys.stdout.isatty():
        formatter = ColoredFormatter(
            '%(asctime)s %(log_color)s%(message)s%(reset)s', "%H:%M:%S")
        stream = logging.StreamHandler()
        stream.setLevel(log_level)
        stream.setFormatter(formatter)
        log = logging.getLogger('pythonConfig')
        log.setLevel(log_level)
        log.addHandler(stream)
    else:
        logging.basicConfig(
            format='%(asctime)s %(message)s', datefmt="%H:%M:%S")
        log = logging


def stats(args):
    if args.country:
        france = []
        files = [path.join(STATS_PATH, x) for x in os.listdir(
            STATS_PATH) if x.endswith('.geojson') and x != "france.geojson"]
        files.sort()
        counter = 0
        for json_path in files:
            counter += 1
            log.info("{:.2f}% Treating {}".format(
                100 * counter / len(files), json_path))
            with open(json_path) as fd:
                department = geojson.load(fd)

            for city in department.features:
                if city.geometry:
                    [x1, x2, y1, y2] = pygeoj.load(
                        data=FeatureCollection([city])).bbox
                    city.geometry = Polygon(
                        [[(x1, y1), (x1, y2), (x2, y2), (x2, y1)]])
                france.append(city)

        json_path = path.join(STATS_PATH, "france.geojson")
        with open(json_path, 'w') as fd:
            fd.write(geojson.dumps(FeatureCollection(france), indent=1))
    elif args.department:
        vectorized = get_vectorized_insee(args.department)
        build_municipality_list(args.department.zfill(
            2), vectorized, force_download=args.force, umap=args.umap, database=args.database)
    elif args.insee:
        vectorized = {}
        for insee in args.insee:
            department = department_for(insee)
            vectorized[department] = get_vectorized_insee(department)
            build_municipality_list(department,
                                    vectorized[department],
                                    given_insee=insee,
                                    force_download=args.force,
                                    umap=args.umap,
                                    database=args.database)
    elif args.name:
        # if we got a name, we must find the associated INSEE
        args.insee = []
        for name in args.name:
            args.insee.append(get_insee_for(name))
        stats(args)
    else:
        log.critical("Unhandled case")


def generate(args):
    insee = get_insee_for(args.name) if args.name else args.insee

    url = 'http://cadastre.openstreetmap.fr'
    data = {
        'dep': department_for(insee).zfill(3),
        'type': 'bati',
        'force': False
    }

    # First we need to get Cadastre name for the city (which is different from
    # the OSM one)
    r = requests.get(
        "http://cadastre.openstreetmap.fr/data/{}/{}-liste.txt".format(data['dep'], data['dep']))
    for line in r.text.split('\n'):
        if '{} "'.format(insee[-3:]) in line:
            linesplit = line.split(' ')
            data[
                'ville'] = "{}-{}".format(linesplit[1], linesplit[2].replace('"', ''))
            break

    if 'ville' not in data:
        log.critical('Cannot find city for {}.'.format(insee))
        exit(1)

    output_path = path.join(BASE_PATH, data['ville'])
    # if data already exists, exit
    if path.exists(output_path):
        log.info("{} has already been downloaded".format(output_path))
        return output_path

    # otherwise we invoke Cadastre generation
    with closing(requests.post(url, data=data, stream=True)) as r:
        for line in r.iter_lines(decode_unicode=True):
            # only display progression
            # TODO: improve this…
            if "pdf" in line:
                log.info(line)

    output_archive_path = path.join(
        BASE_PATH, "{}-{}".format(insee, data['ville']))
    tarname = output_archive_path + '.tar.bz2'
    r = requests.get(
        "http://cadastre.openstreetmap.fr/data/{}/{}.tar.bz2".format(data['dep'], data['ville']))
    log.debug('Uncompressing archive file {}'.format(tarname))
    with open(tarname, 'wb') as fd:
        fd.write(r.content)

    # finally decompress it and move to archive
    tar = tarfile.open(tarname)
    tar.extractall(path=output_archive_path)
    tar.close()
    shutil.move(tarname, path.join(WORKDONETAR_PATH, path.basename(tarname)))

    return output_path


def work(args):
    if args.name:
        args.insee = get_insee_for(args.name)
        args.name = None

    # 1. we should display current state for the city
    # must make a copy because stats expect an array of INSEE instead
    args2 = copy.copy(args)
    args2.insee = [args.insee]
    args2.database = None
    args2.force_download = 'buildings'
    args2.country = False
    args2.department = None
    args2.force = 'buildings'
    args2.umap = ''
    stats(args2)

    # 2. we must generate data from the Cadastre
    city_path = generate(args)

    # 3. start JOSM
    base_url = 'http://0.0.0.0:8111/'

    # a. ensure JOSM is running
    try:
        r = requests.get(base_url + 'version')
    except:
        start_josm(base_url)

    # b. open Strava and BDOrtho IGN imageries
    imageries = OrderedDict([
        ("BDOrtho IGN",
         "http://proxy-ign.openstreetmap.fr/bdortho/{zoom}/{x}/{y}.jpg"),
        ("Strava",
         "http://globalheat.strava.com/tiles/both/color2/{zoom}/{x}/{y}.png"),
    ])
    for k, v in imageries.items():
        r = requests.get(
            base_url + 'imagery?title={}&type=tms&url={}'.format(k, v))
        if r.status_code != 200:
            log.critical("Cannot add imagery ({}): {}".format(
                r.status_code, r.text))

    # c. open both houses-simplifie.osm and houses-prediction_segmente.osm
    # files
    files = [path.join(city_path, x) for x in os.listdir(city_path)
             if x.endswith('-houses-simplifie.osm') or x.endswith('-houses-prediction_segmente.osm')]
    files.sort()
    for x in files:
        r = requests.get(base_url + 'open_file?filename={}'.format(x))
        if r.status_code != 200:
            error = r.text
            if r.status_code == 403:
                error = "did you enable 'Open local files' in Remote Control Preferences?"

            log.critical("Cannot launch JOSM ({}): {}".format(
                r.status_code, error))
            break

    # d. download city data from OSM as well
    bbox = get_bbox_for(args.insee)
    url = base_url + 'load_and_zoom?new_layer=true&layer_name=Données OSM pour {}&left={}&right={}&bottom={}&top={}'
    url = url.format(args.insee, bbox[0], bbox[1], bbox[2], bbox[3])
    r = requests.get(url)
    if r.status_code != 200:
        log.critical("Cannot load OSM data ({}): {}".format(
            r.status_code, r.text))

    resp = None
    while resp not in ["yes", "no"]:
        resp = input("Is the job done? (yes/No)")
        if resp.lower() == "yes":
            log.info("Congratulations! Moving {} to archives".format(city_path))
            shutil.move(city_path, path.join(WORKDONE_PATH, city_path))
            # also regenerate stats
            stats(args2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Inspection de l'état du bâti dans OpenStreetMap en France.")
    parser.add_argument('--verbose', '-v', choices=[
                        'debug', 'info', 'warning', 'error', 'no'], default='info', help="Niveau de verbosité")
    parser.add_argument('--overpass', choices=['overpass.de', 'api.openstreetmap.fr', 'localhost'],
                        default='overpass.de', help="Adresse du serveur pour les requêtes Overpass")
    subparsers = parser.add_subparsers(
        help="Plusieurs commandes sont disponibles")
    subparsers.required = True
    subparsers.dest = 'command'
    stats_parser = subparsers.add_parser(
        'stats', help="Récupère la date du dernier import pour une commune ou un département ou la France entière et génère un .geojson pour une utilisation externe")
    stats_parser.add_argument('--umap', action='store_true',
                              help="À utiliser si le geojson est à destination de UMap")
    stats_parser.add_argument('--force', '-f', choices=['all', 'buildings', 'relations'],
                              default='', help="De ne pas utiliser les fichiers en cache et forcer la requête Overpass")
    stats_parser.add_argument(
        '--database', type=str, help="identifiants pour la base de donnée sous la forme host:port:user:password:database (ex: 'localhost:25432:docker:docker:gis')")
    stats_group = stats_parser.add_mutually_exclusive_group(required=True)
    stats_group.add_argument(
        '--country', '-c', action='store_true', help="France entière")
    stats_group.add_argument('--department', '-d',
                             type=str, help="Département entier")
    stats_group.add_argument('--insee', '-i', type=str,
                             nargs='+', help="commune par son numéro INSEE")
    stats_group.add_argument('--name', '-n', type=str,
                             nargs='+', help="commune par son nom")
    stats_group.set_defaults(func=stats)

    generate_parser = subparsers.add_parser(
        'generate', help="Génère le bâti depuis le cadastre")
    generate_group = generate_parser.add_mutually_exclusive_group(
        required=True)
    generate_group.add_argument(
        '--insee', '-i', type=str, help="commune par son numéro INSEE")
    generate_group.add_argument(
        '--name', '-n', type=str, help="commune par son nom")
    generate_parser.set_defaults(func=generate)

    work_parser = subparsers.add_parser(
        'work', help="Met en place JOSM pour effectuer le travail de mise à jour du bâti")
    work_group = work_parser.add_mutually_exclusive_group(required=True)
    work_group.add_argument('--insee', '-i', type=str,
                            help="commune par son numéro INSEE")
    work_group.add_argument('--name', '-n', type=str,
                            help="commune par son nom")
    work_parser.set_defaults(func=work)

    args = parser.parse_args()
    init_log(args)
    init_overpass(args)
    args.func(args)
