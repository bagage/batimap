import gevent.monkey
gevent.monkey.patch_all()

import os
import logging

from flask import Flask, g
from flask_cors import CORS

from batimap.extensions import celery, batimap, overpass

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    app.config.from_pyfile(app.root_path + "/app.conf")

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
        level=verbosity[os.environ.get("BATIMAP_VERBOSITY") or app.config["VERBOSITY"] or ("DEBUG" if app.config["DEBUG"] else "CRITICAL")],
    )

    from . import db
    db.init_app(app)
    overpass.init_app(app.config["OVERPASS_URI"])
    with app.app_context():
        batimap.init_app(db.get_db(), overpass)

    from . import cli
    from . import api
    app.register_blueprint(cli.app.bp)
    app.register_blueprint(api.routes.bp)

    init_celery(app)

    return app


def init_celery(app=None):
    app = app or create_app()

    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_BACK_URL"]
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
