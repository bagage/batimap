import geojson

from db_utils import Postgis

from flask import abort, Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
from shutil import which
from subprocess import Popen

app = Flask(__name__)
CORS(app)

app.config.from_pyfile(app.root_path + '/app.conf')

db = Postgis(app.config['DB_NAME'],
             app.config['DB_USER'],
             app.config['DB_PASSWORD'],
             app.config['DB_PORT'],
             app.config['DB_HOST'])


@app.route('/')
def index() -> object:
    return render_template('index.html')


@app.route('/insee/<int:insee>', methods=['GET'])
def api_insee(insee) -> dict:
    color_city = db.get_insee(insee)
    return geojson.dumps(color_city)


@app.route('/colors/<lonNW>/<latNW>/<lonSE>/<latSE>/<colors>', methods=['GET'])
def api_color(colors, lonNW, latNW, lonSE, latSE) -> dict:
    color_city = db.get_city_with_colors(colors.split(','), float(lonNW), float(latNW), float(lonSE), float(latSE))
    return geojson.dumps(color_city)


@app.route('/colors', methods=['GET'])
def api_colors_list() -> dict:
    return jsonify(db.get_colors())


@app.route('/status/<department>', methods=['GET'])
def api_status(department) -> dict:
    return jsonify(db.get_department_colors(department))


@app.route('/update/<insee>', methods=['POST'])
def update_insee_list(insee) -> dict:
    r = which("osm-cadastre.py")
    if not r:
        return abort(500)
    child = Popen(["osm-cadastre.py", "stats", "-f", "all", "-i", insee])
    child.communicate()
    child.wait()
    if child.returncode != 0:
        return abort(500)
    return "Ok"


@app.route('/static/<path:path>', methods=['GET'])
def send_resources(path):
    return send_from_directory('static/', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
