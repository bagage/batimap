from celery import Celery

from batimap.batimap import Batimap
from batimap.db import Db
from batimap.overpass import Overpass
from batimap.odcadastre import ODCadastre

from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy

sqlalchemy = SQLAlchemy()
db = Db()

api_smorest = Api()
overpass = Overpass()
batimap = Batimap()
celery = Celery()
odcadastre = ODCadastre()
