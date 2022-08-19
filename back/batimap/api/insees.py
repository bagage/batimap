from batimap.extensions import db

from .routes import bp


@bp.route("/insees/<insee>/osm_id", methods=["GET"])
def api_city_osm_id(insee) -> dict:
    (osm_id,) = db.get_osm_id(insee)
    return str(osm_id)
