import pytest

from datetime import datetime
from batimap.extensions import odcadastre, db
from batimap.db import City


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

        cadastre = odcadastre.compute_count(insee)
        assert cadastre.insee == insee
        if exact_match:
            assert cadastre.od_buildings == count
        else:
            assert cadastre.od_buildings >= count
        assert cadastre.last_fetch > now
