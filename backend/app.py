import geojson
from flask import Flask, jsonify
from flask_cors import CORS

from batimap import batimap
from db_utils import Postgis
from batimap.overpassw import Overpass

app = Flask(__name__)
CORS(app)

app.config.from_pyfile(app.root_path + '/app.conf')

db = Postgis(app.config['DB_NAME'],
             app.config['DB_USER'],
             app.config['DB_PASSWORD'],
             app.config['DB_PORT'],
             app.config['DB_HOST'])

op = Overpass(app.config['OVERPASS_URI'])


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


if __name__ == '__main__':
    app.run(host='0.0.0.0')
