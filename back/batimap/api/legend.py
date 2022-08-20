from batimap.bbox import Bbox
from batimap.extensions import db
from flask import jsonify

from .routes import bp


@bp.route("/legend/<lonNW>/<latNW>/<lonSE>/<latSE>", methods=["GET"])
def api_legend(lonNW, latNW, lonSE, latSE) -> dict:
    result = db.get_imports_count_for_bbox(
        Bbox(float(lonNW), float(latSE), float(lonSE), float(latNW))
    )
    total = sum([x[1] for x in result])

    return jsonify(
        [
            {
                "name": import_date,
                "count": count,
                "percent": round(count * 100.0 / total, 2),
            }
            for (import_date, count) in result
        ]
    )
