#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gevent.monkey
gevent.monkey.patch_all()

import click
import itertools
import logging

from flask import Flask, request
from flask_restful import inputs
from flask_cors import CORS

import json

from batimap import batimap
from batimap.city import City
from citydto import CityEncoder, CityDTO
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

# ROUTES


@app.route('/status', methods=['GET'])
def api_status() -> dict:
    return json.dumps(db.get_dates_count())


@app.route('/status/<department>', methods=['GET'])
def api_department_status(department) -> str:
    return json.dumps([{x[0].insee: x[1]} for x in
                      batimap.stats(db, op, department=department, force=request.args.get('force', False))])


@app.route('/status/<department>/<city>', methods=['GET'])
def api_city_status(department, city) -> str:
    for (city, date) in batimap.stats(db,
                                      op,
                                      cities=[city],
                                      force=request.args.get('force', default=False, type=inputs.boolean)):
        return json.dumps({city.insee: date})
    return ''


@app.route('/status/by_date/<date>')
def api_cities_for_date(date) -> str:
    return json.dumps(db.get_cities_for_date(date))


@app.route('/insee/<insee>', methods=['GET'])
def api_insee(insee) -> dict:
    color_city = db.get_insee(insee)
    return json.dumps(color_city)


@app.route('/cities/in_bbox/<lonNW>/<latNW>/<lonSE>/<latSE>', methods=['GET'])
def api_color(lonNW, latNW, lonSE, latSE) -> dict:
    cities = db.get_cities_in_bbox(
        float(lonNW), float(latNW), float(lonSE), float(latSE))
    return json.dumps(cities, cls=CityEncoder)


@app.route('/legend/<lonNW>/<latNW>/<lonSE>/<latSE>', methods=['GET'])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    return json.dumps(db.get_legend_in_bbox(
        float(lonNW), float(latNW), float(lonSE), float(latSE)))


@app.route('/cities/<insee>/update', methods=['POST'])
def api_update_insee_list(insee) -> dict:
    (city, date) = next(batimap.stats(db, op, cities=[insee], force=True))

    # TODO: only clear tiles if color was changed // return different status
    # codes

    # clear tiles for the zone
    db.clear_tiles(insee)
    return json.dumps(CityDTO(city, date), cls=CityEncoder)


@app.route('/cities/<insee>/josm', methods=['GET'])
def api_josm_data(insee) -> dict:
    batimap.fetch_cadastre_data(City(db, insee))
    return json.dumps(batimap.josm_data(db, insee))


# CLI
@app.cli.command('initdb')
@click.argument('departments', nargs=-1)
def initdb_command(departments):
    """
    Creates required tables in PostgreSQL server.
    """
    db.create_tables()

    # fill table with cities from cadastre website
    batimap.update_departments_raster_state(db, departments or db.get_departments())

    db.import_city_stats_from_osmplanet(departments or db.get_departments())


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
        d = db.get_departments()
        c = None
    elif region == 'department':
        d = items
        c = None
    else:
        d = [None]
        c = items

    for department in d:
        for (city, date) in batimap.stats(db,
                                          op,
                                          department=department,
                                          cities=c,
                                          force=not fast,
                                          refresh_cadastre_state=not fast):
            click.echo('{}: date={}'.format(city, date))
