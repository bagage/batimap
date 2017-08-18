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


# ROUTES
@app.route('/insee/<int:insee>', methods=['GET'])
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
@app.cli.command('initdb', help='Create tables')
def initdb_command():
    db.create_tables()


@app.cli.command('update-city-stats')
@click.argument('city')
def update_city_stats(city):
    for (city, date, author) in batimap.stats(db, op, cities=[city], force=True):
        click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('update-department-stats')
@click.argument('department')
def update_department_stats(department):
    for (city, date, author) in batimap.stats(db, op, department=department, force=True):
        click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('update-france-stats')
def update_france_stats():
    for department in itertools.chain(range(1, 20), ('2A', '2B'), range(21, 96), range(971, 977)):
        for (city, date, author) in batimap.stats(db, op, department=department, force=True):
            click.echo('{}: date={} author={}'.format(city, date, author))


@app.cli.command('generate-city-building')
@click.argument('city')
def generate_city_building(city):
    batimap.generate(db, cities=[city])


@app.cli.command('load-city-josm')
@click.argument('city')
def load_city_josm(city):
    batimap.work(db, cities=[city])
