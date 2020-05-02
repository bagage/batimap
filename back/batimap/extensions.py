from celery import Celery
from batimap.batimap import Batimap
from batimap.overpass import Overpass

from flask_smorest import Api

api_smorest = Api()
overpass = Overpass()
batimap = Batimap()
celery = Celery()
