#!/usr/bin/env python3

import logging
import os
from os import path

import geojson
import overpass
from geojson import Feature, Polygon

DATA_PATH = path.normpath(path.join(path.dirname(__file__), '..', 'data'))
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

def build_municipality_list(department):
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

        txt_content += '{},{},{}\n'.format(insee, name, postcode)

        # write geojson
        geojson_path = path.join(BORDER_PATH, '{}.geojson'.format(insee))
        with open(geojson_path, 'w') as fd:
            fd.write(geojson.dumps(municipality_border))

    # write txt
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


if __name__ == '__main__':
    build_municipality_list(38)
