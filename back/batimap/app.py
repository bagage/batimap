import json
import os
import logging

from flask import Flask
from flask_cors import CORS

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from batimap.citydto import CityDTO

from batimap.extensions import (
    api_smorest,
    celery,
    batimap,
    overpass,
    db,
    sqlalchemy,
    odcadastre,
)
from batimap.taskdto import TaskDTO


class BatimapEncoder(json.JSONEncoder):
    def default(self, obj):

        if isinstance(obj, CityDTO) or isinstance(obj, TaskDTO):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(obj)


def create_app(db_uri=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    app.config.from_pyfile(app.root_path + "/app.conf")
    app.config["OPENAPI_VERSION"] = "3.0.2"
    app.config["OPENAPI_URL_PREFIX"] = "/api"
    if db_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    app.json_encoder = BatimapEncoder

    verbosity = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        level=verbosity[
            os.environ.get("BATIMAP_VERBOSITY")
            or app.config["VERBOSITY"]
            or ("DEBUG" if app.config["DEBUG"] else "CRITICAL")
        ],
    )

    sqlalchemy.init_app(app)
    db.init_app(app, sqlalchemy)
    batimap.init_app(db, overpass)
    odcadastre.init_app(db)
    api_smorest.init_app(app)

    from . import cli
    from . import api

    app.register_blueprint(cli.app.bp)

    api_smorest.register_blueprint(api.routes.bp)

    init_celery(app)

    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        app.logger.info("setting up sentry")
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0,
        )

    return app


def init_celery(app=None):
    app = app or create_app()

    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_BACK_URL"]
    celery.conf.task_routes = {
        "batimap.tasks.common.task_josm_data_fast": {"queue": "celery"},
        "batimap.tasks.common.task_update_insee": {"queue": "celery"},
        "batimap.tasks.common.task_initdb": {"queue": "celery_slow"},
        "batimap.tasks.common.task_josm_data": {"queue": "celery_slow"},
    }
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
