#!/usr/bin/env python3

import datetime
import json
import logging
import os
import re
import sys

from os import path

import geojson
import overpass
import requests
from colour import Color
from geojson import Feature, Polygon, FeatureCollection

DATA_PATH = path.normpath(path.join(path.dirname(path.realpath(__file__)), '..', 'data'))
STATS_PATH = path.join(DATA_PATH, 'stats')
BORDER_PATH = path.join(DATA_PATH, 'borders')
os.makedirs(STATS_PATH, exist_ok=True)
os.makedirs(BORDER_PATH, exist_ok=True)

CADASTRE_PROG = re.compile(r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')

API = overpass.API()


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
        logging.warning("Unknown date '{}'! Using gray.".format(dates[0][0]));
        return 'gray'

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


def build_municipality_list(department, vectorized):
    """Build municipality list
    """
    logging.info('Fetch cities boundary for departement {} (overpass-api.de)'.format(department))
    request = """[out:json];
        relation
          [boundary="administrative"]
          [admin_level=8]
          ["ref:INSEE"~"{}..."];
        out geom qt;""".format(department)

    response = API.Get(request, responseformat="json", build=False)

    features = []

    txt_content = ''
    department_stats = []

    for relation in response.get('elements'):
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
        if insee in vectorized:
            vector = 'vector'
            building_src = count_sources('building', insee)
            relation_src = count_sources('relation', insee)
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
            logging.warning('{} does not have borders'.format(name))
        else:
            municipality_border.geometry = Polygon([border])

        department_stats.append(municipality_border)
        txt_content += '{},{},{},{}\n'.format(insee, name, postcode, vector)

    # write geojson
    logging.debug('Write {}.geojson'.format(department))
    geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    with open(geojson_path, 'w') as fd:
        fd.write(geojson.dumps(FeatureCollection(department_stats)))

    # write department geojson
    dep_geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    with open(dep_geojson_path, 'w') as fd:
        fd.write(geojson.dumps(FeatureCollection(features)))

    # write txt
    logging.debug('Write {}-municipality.txt'.format(department))
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


def get_vectorized_insee(department):
    logging.info('Fetch list of vectorized cities in department {}'.format(department))
    vectorized = []
    response = requests.get('http://cadastre.openstreetmap.fr/data/0{0}/0{0}-liste.txt'.format(department))
    for dep, code, _ in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
        vectorized.append('{}{}'.format(dep[1:], code[2:]))
    return vectorized


def count_sources(datatype, insee):
    logging.info('Count {} sources for {} (overpass-api.de)'.format(datatype, insee))

    json_path = path.join(DATA_PATH, '{}.{}.json'.format(insee, datatype))
    if path.exists(json_path):
        logging.debug('Use cache file {}.{}.json'.format(insee, datatype))
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

    response = API.Get(request, responseformat="json", build=False)

    sources = {}
    for element in response.get('elements'):
        src = element.get('tags').get('source') or 'unknown'
        src = src.lower()
        src = re.sub(CADASTRE_PROG, r'\2', src)
        if src not in sources:
            sources[src] = 0
        sources[src] += 1

    logging.debug('Write cache file {}.{}.json'.format(insee, datatype))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(sources))

    return sources


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    if len(sys.argv) != 2:
        logging.error("Please provide ONE argument: department to treat. Example: {} 26".format(sys.argv[0]))
    else:
        department = sys.argv[1]
        vectorized = get_vectorized_insee(department)
        build_municipality_list(department, vectorized)
