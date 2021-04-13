import pytest
from batimap.db import Boundary, City
from batimap.extensions import db


@pytest.fixture
def db_mock_data(app):
    with app.app_context():
        objects = [
            City(insee="01002", import_date="2009"),
            City(insee="01003", import_date="2013"),
            City(insee="01004", import_date="2009"),
            Boundary(
                insee="01002",
                admin_level=8,
                geometry="srid=4326; POLYGON((0 0,1 0,1 1,0 1,0 0))",
            ),
            Boundary(
                insee="01003",
                admin_level=8,
                geometry="srid=4326; POLYGON((1 1,2 1,2 2,1 2,1 1))",
            ),
            Boundary(
                insee="01004",
                admin_level=8,
                geometry="srid=4326; POLYGON((2 2,3 2,3 3,2 3,2 2))",
            ),
        ]
        db.session.add_all(objects)
        db.session.commit()


def test_status_empty(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == []


def test_status(db_mock_data, client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == [{"count": 2, "date": "2009"}, {"count": 1, "date": "2013"}]


@pytest.mark.parametrize(
    ("bboxes", "expected"),
    (
        ([], None),
        ([[0, 0, 1, 1]], ["01002", "01003"]),
        ([[0, 0, 1, 1], [0.4, 0.4, 0.6, 0.6], [0, 0, 0.3, 0.3]], ["01002", "01003"]),
    ),
)
def test_bbox(db_mock_data, client, bboxes, expected):
    resp = client.post("/bbox/cities", json={"bboxes": bboxes})
    assert resp.status_code == 200 if expected else 400
    if expected:
        result = [x["insee"] for x in resp.json]
        assert result == expected
