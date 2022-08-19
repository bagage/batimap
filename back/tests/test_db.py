from batimap.db import Cadastre, City
from batimap.extensions import db


def test_cadastre_city_relationship(app):
    with app.app_context():
        db.session.add(db.session.merge(City(insee="99001")))
        db.session.add(db.session.merge(Cadastre("99001", "99", 90)))
        db.session.commit()

        city = db.get_city_for_insee("99001")
        assert city is not None

        cadastre = db.get_cadastre_for_insee("99001")
        assert cadastre is not None

        assert city.cadastre == cadastre
