import click
import geojson
from flask import Flask, jsonify
from flask_cors import CORS

from batimap import batimap
from batimap.overpassw import Overpass
from db_utils import Postgis

app = Flask(__name__)
CORS(app)

app.config.from_pyfile(app.root_path + '/app.conf')

db = Postgis(app.config['DB_NAME'],
             app.config['DB_USER'],
             app.config['DB_PASSWORD'],
             app.config['DB_PORT'],
             app.config['DB_HOST'])

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
    batimap.stats(db, op, cities=[insee])
    # TODO: only clear tiles if color was changed // return different status
    # codes

    # clear tiles for the zone
    db.clear_tiles(insee)
    return "Ok"


# CLI
@app.cli.command()
@click.argument('city')
def update_city_stats(city):
    batimap.stats(db, op, cities=[city])


@app.cli.command()
@click.argument('department')
def update_department_stats(department):
    batimap.stats(db, op, department=department)


@app.cli.command()
def update_france_stats():
    for r in (range(1, 20), ('2A', '2B'), range(21, 96), range(971, 977)):
        for d in r:
            batimap.stats(db, op, department=str(d))


@app.cli.command()
@click.argument('city')
def generate_city_building(city):
    batimap.generate(db, cities=[city])


@app.cli.command()
@click.argument('city')
def load_city_josm(city):
    batimap.work(db, cities=[city])
