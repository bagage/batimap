#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import geojson
from flask import Flask, jsonify
from flask_cors import CORS

from batimap import batimap
from batimap.overpassw import Overpass
from db_utils import Postgis

import itertools
import logging

app = Flask(__name__)
app.config.from_pyfile(app.root_path + '/app.conf')
CORS(app)

logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt="%H:%M:%S",
    level=logging.DEBUG if app.config[
        'DEBUG'] else logging.CRITICAL
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
def update_insee_list(insee) -> dict:
    batimap.stats(db, op, cities=[insee], force=True)
    # TODO: only clear tiles if color was changed // return different status
    # codes

    # clear tiles for the zone
    db.clear_tiles(insee)
    return "Ok"


# CLI
@app.cli.command('initdb')
def initdb_command():
    """
    Creates required tables in PostgreSQL server.
    """
    db.create_tables()


@app.cli.command('get-city-stats')
@click.argument('cities', nargs=-1)
@click.option('--fast', is_flag=True)
def get_city_stats(fast, cities):
    """
    Returns cadastral status of given cities.
    If status is unknown, it is computed first.
    """
    for (city, date, author) in batimap.stats(db, op, cities=cities, force=not fast):
        click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('get-department-stats')
@click.argument('departments', nargs=-1)
@click.option('--fast', is_flag=True)
def get_department_stats(fast, departments):
    """
    Returns cadastral status of given departments cities.
    If status is unknown, it is computed first.
    """
    for department in departments:
        for (city, date, author) in batimap.stats(db, op, department=department, force=not fast):
            click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('get-france-stats')
@click.option('--fast', is_flag=True)
def get_france_stats(fast):
    """
    Returns cadastral status of French cities.
    If status is unknown, it is computed first.
    """
    for department in all_departments:
        for (city, date, author) in batimap.stats(db, op, department=department, force=not fast):
            click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('generate-city-building')
@click.argument('cities', nargs=-1)
def generate_city_building(cities):
    """
    Download buildings for given cities. IMPROVE_ME
    """
    batimap.generate(db, cities=cities)


@app.cli.command('load-city-josm')
@click.argument('cities', nargs=-1)
def load_city_josm(cities):
    """
    Create and open JOSM project for given cities.
    """
    batimap.work(db, cities=cities)
