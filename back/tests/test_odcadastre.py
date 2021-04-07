import pytest

from datetime import datetime
from batimap.extensions import odcadastre, db
from batimap.db import City, Cadastre, Boundary


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

        city = City()
        city.insee = insee
        db.session.add(db.session.merge(city))
        db.session.query(Cadastre).delete()

        cadastre = odcadastre.compute_count(insee)
        assert cadastre is not None
        assert cadastre.insee == insee
        if exact_match:
            assert cadastre.od_buildings == count
        else:
            assert cadastre.od_buildings >= count
        assert cadastre.last_fetch > now


def test_department_has_buildings(app):
    with app.app_context():
        now = datetime.now()
        department = "05"

        boundary = Boundary()
        boundary.osm_id = 9999
        boundary.name = "test-dept-05"
        boundary.admin_level = 6
        boundary.insee = department
        db.session.add(db.session.merge(boundary))

        cadastre = odcadastre.compute_count(department)
        assert cadastre is not None
        assert cadastre.department == department
        assert cadastre.od_buildings >= 160000
        assert cadastre.last_fetch > now
