import pytest
from batimap.db import City
from batimap.extensions import db


@pytest.fixture
def db_mock_data(app):
    with app.app_context():
        cities = [
            City(insee="01002", import_date="2009"),
            City(insee="01003", import_date="2013"),
            City(insee="01004", import_date="2009"),
        ]
        db.session.add_all(cities)
        db.session.commit()


def test_status_empty(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == []


def test_status(db_mock_data, app, client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == [{"count": 2, "date": "2009"}, {"count": 1, "date": "2013"}]
