from batimap.extensions import db
from flask import jsonify

from .routes import bp


@bp.route("/departments", methods=["GET"])
def api_departments() -> dict:
    return jsonify(db.get_departments())


@bp.route("/departments/<dept>", methods=["GET"])
def api_department(dept) -> dict:
    d = db.get_department(dept)
    s = dict(db.get_department_import_stats(dept))
    date = max(s, key=s.get)  # type: ignore
    return jsonify({"name": d.name, "date": date, "insee": dept})


@bp.route("/departments/<dept>/details", methods=["GET"])
def api_department_details(dept) -> dict:
    stats = dict(db.get_department_import_stats(dept))
    simplified = sorted(
        [ids for city in db.get_department_simplified_buildings(dept) for ids in city]
    )
    return jsonify({"simplified": simplified, "dates": stats})
