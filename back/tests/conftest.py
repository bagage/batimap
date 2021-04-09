import pytest
import os

from batimap.app import create_app
from batimap.extensions import db
from batimap.db import Base


@pytest.fixture
def app():
    test_db = os.environ.get(
        "POSTGRES_URI", "postgresql://test:batimap@localhost:15432/testdb"
    )

    app = create_app(test_db)
    app.config["TESTING"] = True

    yield app

    with app.app_context():
        Base.metadata.drop_all(bind=db.sqlalchemy.engine)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
