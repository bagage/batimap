from batimap.extensions import db
from batimap.db import City, Cadastre


def test_cadastre_city_relationship(app):
    with app.app_context():
        db.session.add(db.session.merge(City(insee="10001")))
        db.session.add(db.session.merge(Cadastre("10001", "10", 10)))
        db.session.commit()

        city = db.get_city_for_insee("10001")
        assert city is not None

        cadastre = db.get_cadastre_for_insee("10001")
        assert cadastre is not None

        assert city.cadastre == cadastre
