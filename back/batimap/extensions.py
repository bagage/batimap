from batimap.db import Db
from batimap.odcadastre import ODCadastre
from batimap.overpass import Overpass
from celery import Celery
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy

from batimap.batimap import Batimap

sqlalchemy = SQLAlchemy()
db = Db()

api_smorest = Api()
overpass = Overpass()
batimap = Batimap()
celery = Celery()
odcadastre = ODCadastre()
