from batimap.bbox import Bbox
from batimap.citydto import CityDTO
from batimap.extensions import db
from flask import jsonify, request
from flask_smorest import abort

from .routes import bp


@bp.route("/bbox/cities", methods=["POST"])
def api_bbox_cities() -> dict:
    bboxes = (request.get_json() or {}).get("bboxes", [])
    if not bboxes:
        abort(400, message="missing required bboxes")
    cities = set()
    for bbox in bboxes:
        bbox_cities = set(db.get_cities_for_bbox(Bbox(*bbox)))
        cities |= bbox_cities
    return jsonify(sorted([CityDTO(x) for x in cities]))
