from celery import Celery
from batimap.batimap import Batimap
from batimap.overpass import Overpass

overpass = Overpass()
batimap = Batimap()
celery = Celery()
