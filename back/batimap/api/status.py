from batimap.extensions import batimap, db
from flask import jsonify, request
from flask_restful import inputs

from .routes import bp


@bp.route("/status", methods=["GET"])
def api_status() -> str:
    return jsonify(
        [{"date": x[0], "count": x[1]} for x in db.get_imports_count_per_year()]
    )


@bp.route("/status/<department>", methods=["GET"])
def api_department_status(department) -> str:
    return jsonify(
        [
            {x.insee: x.import_date}
            for x in batimap.stats(
                department=department, force=request.args.get("force", False)
            )
        ]
    )


@bp.route("/status/<department>/<city>", methods=["GET"])
def api_city_status(department, city) -> str:
    for city in batimap.stats(
        names_or_insees=[city],
        force=request.args.get("force", default=False, type=inputs.boolean),
    ):
        return jsonify({city.insee: city.import_date})
    return ""


@bp.route("/status/by_date/<date>")
def api_cities_for_date(date) -> str:
    return jsonify(db.get_cities_for_year(date))
