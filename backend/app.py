#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gevent.monkey
gevent.monkey.patch_all()

import click
import geojson
import itertools
import logging

from flask import Flask, jsonify, request
from flask_restful import inputs
from flask_cors import CORS

from batimap import batimap
from batimap.overpassw import Overpass
from db_utils import Postgis

app = Flask(__name__)
app.config.from_pyfile(app.root_path + '/app.conf')
CORS(app)

LOG = logging.getLogger(__name__)

verbosity = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERRROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}
logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt="%H:%M:%S",
    level=verbosity[app.config['VERBOSITY'] or ('DEBUG' if app.config['DEBUG'] else 'CRITICAL')]
)

db = Postgis(
    app.config['DB_NAME'],
    app.config['DB_USER'],
    app.config['DB_PASSWORD'],
    app.config['DB_PORT'],
    app.config['DB_HOST'],
    app.config['TILESERVER_URI'],
)

op = Overpass(app.config['OVERPASS_URI'])

all_departments = itertools.chain(
    range(1, 20), ('2A', '2B'), range(21, 96), range(971, 977))

# ROUTES


@app.route('/status/<department>', methods=['GET'])
def api_department_status(department) -> str:
    return jsonify([{x[0].insee: x[1]} for x in
                    batimap.stats(db, op, department=department, force=request.args.get('force', False))])


@app.route('/status/<department>/<city>', methods=['GET'])
def api_city_status(department, city) -> str:
    for (city, date, author) in batimap.stats(db,
                                              op,
                                              cities=[city],
                                              force=request.args.get('force', default=False, type=inputs.boolean)):
        return jsonify({city.insee: date})
    return ''


@app.route('/status/by_date/<date>')
def api_cities_for_date(date) -> str:
    return jsonify(db.get_cities_for_date(date))


@app.route('/insee/<insee>', methods=['GET'])
def api_insee(insee) -> dict:
    color_city = db.get_insee(insee)
    return geojson.dumps(color_city)


@app.route('/colors/<lonNW>/<latNW>/<lonSE>/<latSE>/<colors>', methods=['GET'])
def api_color(colors, lonNW, latNW, lonSE, latSE) -> dict:
    color_city = db.get_city_with_colors(colors.split(','), float(
        lonNW), float(latNW), float(lonSE), float(latSE))
    return geojson.dumps(color_city)


@app.route('/colors', methods=['GET'])
def api_colors_list() -> dict:
    return jsonify(db.get_colors())


@app.route('/status/<department>', methods=['GET'])
def api_status(department) -> dict:
    return jsonify(db.get_department_colors(department))


@app.route('/update/<insee>', methods=['POST'])
def api_update_insee_list(insee) -> dict:
    (_, date, _) = next(batimap.stats(db, op, cities=[insee], force=True))
    # TODO: only clear tiles if color was changed // return different status
    # codes

    # clear tiles for the zone
    db.clear_tiles(insee)
    return jsonify(date)


@app.route('/josm/<insee>', methods=['GET'])
def api_josm_data(insee) -> dict:
    return jsonify(batimap.josm_data(db, insee))


# CLI
@app.cli.command('initdb')
def initdb_command():
    """
    Creates required tables in PostgreSQL server.
    """
    db.create_tables()

    # fill table with cities from cadastre website
    for d in all_departments:
        batimap.update_department_raster_state(db, d)


@app.cli.command('stats')
@click.argument('items', nargs=-1)
@click.option('--region', type=click.Choice(['city', 'department', 'france']))
@click.option('--fast', is_flag=True)
def get_city_stats(items, region, fast):
    _get_city_stats(items, region, fast)


def _get_city_stats(items, region, fast):
    """
    Returns cadastral status of given items.
    If status is unknown, it is computed first.
    """
    if region == 'france':
        d = all_departments
        c = None
    elif region == 'department':
        d = items
        c = None
    else:
        d = [None]
        c = items

    for department in d:
        for (city, date) in batimap.stats(db, op, department=department, cities=c, force=not fast):
            click.echo('{}: date={}'.format(city, date))
