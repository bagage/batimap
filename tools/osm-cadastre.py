#!/usr/bin/env python3

import datetime
import logging
import os
import sys
from os import path

import geojson
import overpass
import requests
from colour import Color
from geojson import Feature, Polygon

DATA_PATH = path.normpath(path.join(path.dirname(path.realpath(__file__)), '..', 'data'))
STATS_PATH = path.join(DATA_PATH, 'stats')
BORDER_PATH = path.join(DATA_PATH, 'borders')
os.makedirs(STATS_PATH, exist_ok=True)
os.makedirs(BORDER_PATH, exist_ok=True)


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


def color_for_insee(department, insee):
    colors = {
        "RASTER": "Black",
        None: "Gray",
    }

    stats_path = path.join(STATS_PATH, '{}-statistics.csv'.format(department))
    if not os.path.isfile(stats_path):
        logging.warning("{} does not exist, cannot find color for {}".format(stats_path, insee))
        return colors[None]

    with open(stats_path, 'r') as file:
        for line in file:
            fields = [x.strip() for x in line.split("\t")]
            if insee == fields[0]:
                date = fields[5]

                # Retrieve the last cadastre import for the given insee municipality.
                # 2009 and below should be red,
                # current year should be green
                # previous year should be orange
                # below 2009 and previous year, use a color gradient
                this_year = datetime.datetime.now().year
                gradient_colors = list(Color("red").range_to(Color("orange"), this_year - 2009))
                for year in range(2009, this_year):
                    colors[str(year)] = gradient_colors[year - 2009].hex
                colors[str(this_year)] = "Green"

                if date in colors:
                    return colors[date]
                else:
                    logging.warning("Unknown date '{}'! Using gray.".format(date));
                    return "Gray"

    return colors[None]


def build_municipality_list(department, vectorized):
    """Build municipality list
    """
    api = overpass.API()
    response = api.Get('''[out:json];
        relation
            [boundary="administrative"]
            [admin_level=8]
            ["ref:INSEE"~"{}..."];
        out geom qt;'''.format(department),
        responseformat="json",
        build=False,
    )

    features = []

    txt_content = ''
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

        municipality_border = Feature(
            properties={
                'insee': insee,
                'name': name,
                'postcode': postcode,
                '_storage_options': {
                    'color': color_for_insee(department, insee),
                    'weight': '1',
                    'fillOpacity': '0.5',
                },
            },
        )
        border = lines_to_polygon(outer_ways)
        if not border:
            logging.warning('{} does not have borders'.format(name))
        else:
            municipality_border.geometry = Polygon([border])

        vector = 'vector' if insee in vectorized else 'raster'
        txt_content += '{},{},{},{}\n'.format(insee, name, postcode, vector)

        # write municipality geojson
        muni_geojson_path = path.join(BORDER_PATH, '{}.geojson'.format(insee))
        with open(muni_geojson_path, 'w') as fd:
            fd.write(geojson.dumps(municipality_border))

    # write department geojson
    dep_geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    with open(dep_geojson_path, 'w') as fd:
        fd.write(geojson.dumps(FeatureCollection(features)))

    # write txt
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


def get_vectorized_insee(department):
    vectorized = []
    response = requests.get('http://cadastre.openstreetmap.fr/data/0{0}/0{0}-liste.txt'.format(department))
    for dep, code, _ in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
        vectorized.append('{}{}'.format(dep[1:], code[2:]))
    return vectorized


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) != 2:
        logging.error("Please provide ONE argument: department to treat. Example: {} 26".format(sys.argv[0]))
    else:
        department = sys.argv[1]
        vectorized = get_vectorized_insee(department)
        build_municipality_list(department, vectorized)
