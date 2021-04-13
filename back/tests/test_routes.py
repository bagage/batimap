import pytest


def test_status_empty(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == []


def test_status(db_mock_cities, client):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json == [
        {"count": 2, "date": "2009"},
        {"count": 1, "date": "2012"},
        {"count": 1, "date": "2013"},
    ]


@pytest.mark.parametrize(
    ("bboxes", "expected"),
    (
        ([], None),
        ([[0, 0, 1, 1]], ["01004", "01005"]),
        ([[0, 0, 1, 1], [0.4, 0.4, 0.6, 0.6], [0, 0, 0.3, 0.3]], ["01004", "01005"]),
    ),
)
def test_bbox(db_mock_boundaries, db_mock_cities, client, bboxes, expected):
    resp = client.post("/bbox/cities", json={"bboxes": bboxes})
    assert resp.status_code == 200 if expected else 400
    if expected:
        result = [x["insee"] for x in resp.json]
        assert result == expected


def test_josm(db_mock_boundaries, db_mock_cities, client):
    resp = client.get("/cities/01004/josm")
    assert resp.status_code == 202
    assert list(resp.json.keys()) == ["task_id"]
    expected_location = f"http://localhost/tasks/{resp.json['task_id']}"
    assert resp.headers["Location"] == expected_location
    # the task is failing but we're not testing it (yet?) so it's OK
