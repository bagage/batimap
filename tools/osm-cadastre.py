#!/usr/bin/env python3

import datetime
import json
import os
import re
import sys
import subprocess

import logging
from colorlog import ColoredFormatter

import  argparse

from os import path

import geojson
import overpass
import requests
from colour import Color
from geojson import Point, Feature, Polygon, FeatureCollection

import visvalingamwyatt as vw

DATA_PATH = path.normpath(path.join(path.dirname(path.realpath(__file__)), '..', 'data'))
STATS_PATH = path.join(DATA_PATH, 'stats')
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
    this_year = datetime.datetime.now().year
    colors = list(Color('red').range_to(Color('orange'), this_year - 2009))
    colors.append(Color('green'))
    return dict(zip(range(2009, this_year + 1), [c.hex for c in colors]))


COLORS = init_colors()


def pseudo_distance(p1, p2):
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2


def lines_to_polygon(ways):
    if not ways:
        return []

    border = ways.pop(0)
    while ways:
        dist = -1
        closest = 0
        reverse = False
        for i in range(len(ways)):
            d = pseudo_distance(border[-1], ways[i][0])
            if dist > d or i == 0:
                dist = d
                closest = i
                reverse = False
            d = pseudo_distance(border[-1], ways[i][-1])
            if dist > d:
                dist = d
                closest = i
                reverse = True
        n = ways.pop(closest)
        if reverse:
            n.reverse()
        if dist == 0:
            n.pop(0)
        border += n

    return border


def color_by_stats(building_src, relation_src):
    dates = sorted(building_src.items(), key=lambda t: t[1])
    dates.reverse()
    try:
        date = int(dates[0][0])
    except:
        if len(dates) > 0:
            if dates[0][0] != "unknown":
                log.warning('Unknown date "{}"! Using gray.'.format(dates[0][0]));
            return 'gray'
        else:
            log.warning('No buildings found! Using pink.');
            return 'pink'

    if date <= 2009:
        return '#f00'
    else:
        return COLORS[date]


def stats_to_txt(stats):
    out = ''
    dates = sorted(stats.items(), key=lambda t: t[1])
    dates.reverse()
    total = sum(stats.values())
    for date, val in dates:
        out += '{}\t{} ({:.1%})\n'.format(date, val, val/total)
    out += 'Total\t{}\n'.format(total)
    return out


def get_municipality_relations(department, insee=None, force_download=False):
    log.info('Fetch cities boundary for department {} (via {})'.format(department, API.endpoint))

    json_path = path.join(STATS_PATH, '{}-limits.json'.format(department))

    if not force_download and path.exists(json_path) and not insee:
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            return json.load(fd)

    request = """[out:json];
        relation
          [boundary="administrative"]
          [admin_level=8]
          ["ref:INSEE"~"^{}"];
        out geom qt;""".format(insee if insee else department)

    response = API.Get(request, responseformat='json', build=False)

    relations = response.get('elements')
    relations.sort(key=lambda x: x.get('tags').get('ref:INSEE'))

    if not insee:
        log.debug('Write cache file {}'.format(json_path))
        with open(json_path, 'w') as fd:
            fd.write(json.dumps(relations))

    return relations

def build_municipality_list(department, vectorized, insee=None, force_download=False):
    """Build municipality list
    """
    department = department.zfill(2)

    features = []
    txt_content = ''
    department_stats = []

    counter = 0
    relations = get_municipality_relations(department, insee, force_download)
    for relation in relations:
        counter += 1
        outer_ways = []
        for member in relation.get('members'):
            if member.get('role') == 'outer':
                way = []
                for point in member.get('geometry'):
                    way.append((point.get('lon'), point.get('lat')))
                outer_ways.append(way)

        tags = relation.get('tags')
        insee = tags.get('ref:INSEE')
        name = tags.get('name')
        postcode = tags.get('addr:postcode')

        log.info("{:.2f}% Treating {} - {}".format(100 * counter / len(relations), insee, name))
        if insee in vectorized:
            vector = 'vector'
            try:
                relation_src = count_sources('relation', insee, force_download)
                building_src = count_sources('building', insee, force_download)
            except overpass.errors.ServerRuntimeError as e:
                log.error("Fail to query overpass for {}. Consider reporting the bug: {}. Skipping".format(insee, e))
                continue

            color = color_by_stats(building_src, relation_src)
            description = 'Building:\n{}\nRelation:\n{}'.format(stats_to_txt(building_src), stats_to_txt(relation_src))
        else:
            vector = 'raster'
            color = 'black'
            description = 'Raster'

        municipality_border = Feature(
            properties={
                'insee': insee,
                'name': name,
                'postcode': postcode,
                'description': description,
                '_storage_options': {
                    'color': color,
                    'weight': '1',
                    'fillOpacity': '0.5',
                    'labelHover': True,
                },
            },
        )
        border = lines_to_polygon(outer_ways)
        if not border:
            log.warning('{} does not have borders'.format(name))
        else:
            municipality_border.geometry = Polygon([border])

        department_stats.append(municipality_border)
        txt_content += '{},{},{},{}\n'.format(insee, name, postcode, vector)

    # write geojson
    log.debug('Write {}.geojson'.format(department))
    geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    with open(geojson_path, 'w') as fd:
        # we should not indent the GeoJSON because it drastically reduce the final size
        # (x10 or so)
        fd.write(geojson.dumps(FeatureCollection(department_stats), indent=None))

    # write txt
    log.debug('Write {}-municipality.txt'.format(department))
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


def get_vectorized_insee(department):
    department = department.zfill(2)
    log.info('Fetch list of vectorized cities in department {}'.format(department))
    json_path = path.join(STATS_PATH, '{}-cadastre.json'.format(department))

    if path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            return json.load(fd)


    vectorized = []
    response = requests.get('http://cadastre.openstreetmap.fr/data/{0}/{0}-liste.txt'.format(department.zfill(3)))
    if response.status_code >= 400:
        log.critical('Unknown department {}'.format(department))
        exit(1)

    for _, code, _ in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
        if code.isdigit() and int(code) > 95:
            vectorized.append('{}{}'.format(department, code[3:]))
        else:
            vectorized.append('{}{}'.format(department, code[2:]))

    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(vectorized, indent=4))

    return vectorized


def count_sources(datatype, insee, force_download):
    log.info('Count {} sources for {} (via {})'.format(datatype, insee, API.endpoint))

    json_path = path.join(DATA_PATH, '{}.{}.json'.format(insee, datatype))
    if not force_download and path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            return json.load(fd)

    if datatype == 'building':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( node['building'](area.a);
              way['building'](area.a);
              relation['building'](area.a);
            );
            out tags qt;""".format(insee)
    elif datatype == 'relation':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( way['building'](area.a);
              node(w)['addr:housenumber'];
            );
            out tags qt;""".format(insee)

    response = API.Get(request, responseformat='json', build=False)

    sources = {}
    for element in response.get('elements'):
        src = element.get('tags').get('source') or 'unknown'
        src = src.lower()
        src = re.sub(CADASTRE_PROG, r'\2', src)
        if src not in sources:
            sources[src] = 0
        sources[src] += 1

    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(sources, indent=4))

    return sources


def init_overpass(args):
    endpoints = {
        'overpass.de': 'https://overpass-api.de/api/interpreter',
        'api.openstreetmap.fr': 'http://api.openstreetmap.fr/oapi/interpreter',
        'localhost': 'http://localhost:5001/api/interpreter' #default port/url for docker image
    }
    global API

    API = overpass.API(endpoint=endpoints[args.overpass], timeout=100)

def init_log(args):
    levels = {
        "no": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    global log
    LOG_LEVEL = levels[args.verbose]
    logging.root.setLevel(LOG_LEVEL)
    if sys.stdout.isatty():
        formatter = ColoredFormatter('%(asctime)s %(log_color)s%(message)s%(reset)s', "%H:%M:%S")
        stream = logging.StreamHandler()
        stream.setLevel(LOG_LEVEL)
        stream.setFormatter(formatter)
        log = logging.getLogger('pythonConfig')
        log.setLevel(LOG_LEVEL)
        log.addHandler(stream)
    else:
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt="%H:%M:%S")
        log = logging

def stats(args):
    if args.department:
        vectorized = get_vectorized_insee(args.department)
        build_municipality_list(args.department.zfill(2), vectorized, force_download=args.force)
    elif args.insee:
        vectorized = {}
        for insee in args.insee:
            if insee.isdigit() and int(insee) > 96000:
                department =  insee[:-2]
            else:
                department =  insee[:-3]
            vectorized[department] = get_vectorized_insee(department)
            build_municipality_list(department, vectorized[department], insee=insee, force_download=args.force)

def generate(args):
    url = 'http://cadastre.openstreetmap.fr'
    data = {
        'dep': args.insee[:-3].zfill(3),
        'type': 'bati',
        'force': False
    }

    # First we need to get Cadastre name for the city (which is different from the OSM one)
    r = requests.get("http://cadastre.openstreetmap.fr/data/{}/{}-liste.txt".format(data['dep'], data['dep']))
    for line in r.text.split('\n'):
        if '{} "'.format(args.insee[3:]) in line:
            linesplit = line.split(' ')
            data['ville'] = "{}-{}".format(linesplit[1],linesplit[2])
            break

    if 'ville' not in data:
        log.critical('Cannot find city for {}.'.format(args.insee))
        exit(1)

    #  Then we invoke Cadastre generation
    response = subprocess.Popen(['curl', '-N', url, '-d', '&'.join(["{}={}".format(k, v) for (k,v) in data.items()])])
    response.wait()

    r = requests.get("http://cadastre.openstreetmap.fr/data/{}/{}.tar.bz2".format(data['dep'], data['ville']))

    output_path = path.join(DATA_PATH, "{}.tar.bz2".format(data['ville']))
    log.debug('Write archive file {}'.format(output_path))
    with open(output_path, 'wb') as fd:
        fd.write(r.content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument( '--verbose', '-v', choices=['debug','info','warning','error','no'], default='info')
    parser.add_argument( '--overpass', choices=['overpass.de','api.openstreetmap.fr','localhost'], default='api.openstreetmap.fr')
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'
    stats_parser = subparsers.add_parser('stats')
    stats_parser.add_argument('--force', '-f', action='store_true')
    stats_group = stats_parser.add_mutually_exclusive_group(required=True)
    stats_group.add_argument( '--department', '-d', type=str)
    stats_group.add_argument( '--insee', '-i', type=str, nargs='+')
    stats_group.set_defaults(func=stats)

    generate_parser = subparsers.add_parser('generate')
    generate_parser.add_argument( '--insee', '-i', type=str, required=True)
    generate_parser.set_defaults(func=generate)

    args = parser.parse_args()
    init_log(args)
    init_overpass(args)
    args.func(args)
