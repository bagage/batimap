from datetime import datetime

import pytest
from batimap.db import Boundary, Cadastre, City
from batimap.extensions import db, odcadastre


@pytest.mark.parametrize(
    ("insee", "count", "exact_match"),
    (
        ("55050", 3, True),
        ("14032", 850, False),
    ),
)
def test_city_has_buildings(app, insee, count, exact_match):
    with app.app_context():
        now = datetime.now()

        db.session.query(Cadastre).delete()
        db.session.add(db.session.merge(City(insee=insee)))

        cadastre = odcadastre.compute_count(insee)
        city = db.get_city_for_insee(insee)
        assert cadastre is not None
        assert cadastre == city.cadastre
        assert cadastre.insee == insee
        if exact_match:
            assert cadastre.od_buildings == count
        else:
            assert cadastre.od_buildings >= count
        assert cadastre.last_fetch > now


def test_department_has_buildings(app):
    with app.app_context():
        now = datetime.now()

        boundary = Boundary(osm_id=9999, name="test-dept-05", admin_level=6, insee="05")
        db.session.add(db.session.merge(boundary))

        cadastre = odcadastre.compute_count(boundary.insee)
        assert cadastre is not None
        assert cadastre.department == boundary.insee
        assert cadastre.od_buildings >= 160000
        assert cadastre.last_fetch > now
