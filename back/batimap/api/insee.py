import json

from batimap.extensions import db
from flask import jsonify, Response
from geojson import Feature, FeatureCollection

from .routes import bp


@bp.route("/insee/<insee>", methods=["GET"])
def api_insee(insee) -> Response:
    city = db.get_city_for_insee(insee)
    if city:
        geo = db.get_city_geometry(insee)[0]
        feature = Feature(
            properties={
                "name": f"{city.name} - {city.insee}",
                "date": city.import_date,
            },
            geometry=json.loads(geo),
        )
        return jsonify(
            FeatureCollection(feature)
        )  # fixme: no need for FeatureCollection here
    return f"no city {insee}", 404
