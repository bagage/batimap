import datetime
import os

import pytest
from batimap.app import create_app
from batimap.db import Base, Boundary, Cadastre, City
from batimap.extensions import db


@pytest.fixture
def app():
    test_db_uri = os.environ.get(
        "POSTGRES_URI", "postgresql://test:batimap@localhost:15432/testdb"
    )
    test_redis_uri = os.environ.get("REDIS_URI", "redis://localhost:16379")

    app = create_app(test_db_uri, test_redis_uri)
    app.config.update(
        TESTING=True, CELERY_BROKER_URL=test_redis_uri, CELERY_BACK_URL=test_redis_uri
    )

    yield app

    with app.app_context():
        Base.metadata.drop_all(bind=db.sqlalchemy.engine)
        # pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app, caplog):
    # we need to disable logs because of https://github.com/pallets/click/issues/824
    caplog.set_level(100000)

    return app.test_cli_runner()


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "memory://",
        "result_backend": os.environ.get("REDIS_URI", "redis://localhost:16379"),
    }


@pytest.fixture
def db_mock_cities(app):
    with app.app_context():
        objects = [
            City(insee="01004", department="01", import_date="2009"),
            City(insee="01005", department="01", import_date="2013"),
            City(insee="01006", department="01", import_date="2009"),
            City(insee="02022", department="02", import_date="2012"),
            City(insee="02023", department="02", import_date="raster", is_raster=True),
        ]
        db.session.add_all(objects)
        db.session.commit()


@pytest.fixture
def db_mock_all_date(app):
    with app.app_context():
        dates = list(range(2009, 2021)) + [
            "raster",
            "unfinished",
            "unknown",
            "never",
        ]
        for idx, date in enumerate(dates):
            db.session.add_all(
                [
                    Cadastre(insee=f"080{idx:02}", department="08", od_buildings=100),
                    Cadastre(insee=f"081{idx:02}", department="08", od_buildings=100),
                    City(
                        insee=f"080{idx:02}",
                        department="08",
                        import_date=date,
                        osm_buildings=25,
                    ),
                    City(
                        insee=f"081{idx:02}",
                        department="08",
                        date_cadastre=datetime.datetime.now(),
                        import_date=date,
                        osm_buildings=100,
                    ),
                    Boundary(
                        insee=f"080{idx:02}",
                        admin_level=8,
                        geometry="srid=4326; POLYGON((0 0,0.1 0,0.1 0.1,0 0.1,0 0))",
                    ),
                    Boundary(
                        insee=f"081{idx:02}",
                        admin_level=8,
                        geometry="srid=4326; POLYGON((0 0,0.2 0,0.2 0.2,0 0.2,0 0))",
                    ),
                ]
            )
        db.session.commit()


@pytest.fixture
def db_mock_boundaries(app):
    with app.app_context():
        objects = [
            Boundary(
                insee="01",
                name="01-test",
                geometry="srid=4326; POLYGON((0 0,1 0,1 1,0 1,0 0))",
                admin_level=6,
            ),
            Boundary(
                insee="02",
                name="02-test",
                geometry="srid=4326; POLYGON((0 0,1 0,1 1,0 1,0 0))",
                admin_level=6,
            ),
            Boundary(
                insee="01004",
                name="01004-test",
                admin_level=8,
                geometry="srid=4326; POLYGON((0 0,1 0,1 1,0 1,0 0))",
            ),
            Boundary(
                insee="01005",
                name="01005-test",
                admin_level=8,
                geometry="srid=4326; POLYGON((1 1,2 1,2 2,1 2,1 1))",
            ),
            Boundary(
                insee="01006",
                name="01006-test",
                admin_level=8,
                geometry="srid=4326; POLYGON((2 2,3 2,3 3,2 3,2 2))",
            ),
            Boundary(
                insee="02022",
                name="02022-test",
                admin_level=8,
                geometry="srid=4326; POLYGON((3 3,4 3,4 4,3 4,3 3))",
            ),
            Boundary(
                insee="02022",
                name="02022-test-oldcity",
                admin_level=9,
                geometry="srid=4326; POLYGON((3.5 3.5,4 3.5,4 4,3.5 4,3.5 3.5))",
            ),
            Boundary(
                insee="02023",
                name="02023-test",
                admin_level=8,
                geometry="srid=4326; POLYGON((3 3,4 3,4 4,3 4,3 3))",
            ),
        ]
        db.session.add_all(objects)
        db.session.commit()
