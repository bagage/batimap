from datetime import datetime, timedelta

from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy

from dateutil import parser
from geoalchemy2 import Geometry
from sqlalchemy import Column, Boolean, TIMESTAMP, String, JSON, Integer, BigInteger
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base

from .bbox import Bbox


def get_db():
    if 'db' not in g:
        g.sqlalchemy = SQLAlchemy(current_app)
        g.db = Db(g.sqlalchemy)

    return g.db

def init_app(app):
    app.teardown_appcontext(close_db)

def close_db(e=None):
    sqlalchemy = g.pop('sqlalchemy', None)
    db = g.pop('db', None)

Base = declarative_base()


class City(Base):
    __tablename__ = "city_stats"

    insee = Column(String, primary_key=True)
    department = Column(String)
    name = Column(String)
    name_cadastre = Column(String)
    is_raster = Column(Boolean)
    import_date = Column(String, name="date")
    date_cadastre = Column(TIMESTAMP)
    import_details = Column(JSON, name="details")

    def __repr__(self):
        return f"{self.name}({self.insee})"

    def is_josm_ready(self):
        return self.date_cadastre is not None and (datetime.now() - parser.parse(str(self.date_cadastre))).days < 30

    @staticmethod
    def bad_dates():
        return [None, "unfinished", "unknown", "never"]


class Building(Base):
    __tablename__ = "osm_buildings"

    id = Column(Integer, primary_key=True)
    osm_id = Column(BigInteger)
    name = Column(String)
    source = Column(String)
    source_date = Column(String)
    building = Column(String)
    geometry = Column(Geometry(geometry_type="POLYGON", management=True))


class Boundary(Base):
    __tablename__ = "osm_admin"

    id = Column(Integer, primary_key=True)
    osm_id = Column(BigInteger)
    name = Column(String)
    boundary = Column(String)
    admin_level = Column(Integer)
    insee = Column(String)
    geometry = Column(Geometry(geometry_type="POLYGON", management=True))


class Db(object):
    def __init__(self, db):
        City.metadata.create_all(db.engine)
        self.session = db.session

    @staticmethod
    def __filter_city(query, insee=None):
        filt = query.filter(Boundary.admin_level >= 8)
        return filt.filter(Boundary.insee == insee) if insee else filt

    @staticmethod
    def __build_srid(bbox: Bbox):
        lon = (bbox.xmin + bbox.xmax) / 2.0
        lat = (bbox.ymin + bbox.ymax) / 2.0
        return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    @staticmethod
    def __flat(req):
        return [x[0] for x in req]

    def get_osm_city_name_for_insee(self, insee) -> str:
        # there might be no result for this query, but this is OK
        return self.__filter_city(self.session.query(Boundary.name), insee).first()

    def get_cities_for_department(self, department) -> [City]:
        return self.session.query(City).filter(City.department == department.zfill(2)).order_by(City.insee).all()

    def get_city_for_insee(self, insee) -> City:
        return self.session.query(City).filter(City.insee == insee).first()

    def get_city_for_name(self, name) -> City:
        return self.session.query(City).filter(City.name == name).first()

    def get_city_for_cadastre_name(self, name_cadastre):
        return self.session.query(City).filter(City.name_cadastre == name_cadastre).first()

    def get_osm_id(self, insee) -> int:
        return self.session.query(-1 * Boundary.osm_id).filter(Boundary.insee == insee).first()

    def get_city_bbox(self, insee):
        # first() is required because of multipolygons cities (76218 - Doudeauville for instance)
        return Bbox.from_pg(
            self.__filter_city(self.session.query(func.Box2D(Boundary.geometry)), insee).order_by(Boundary.admin_level).first()[0]
        )

    def get_imports_count_per_year(self):
        return (
            self.session.query(City.import_date, func.count(City.import_date)).group_by(City.import_date).order_by(City.import_date).all()
        )

    def get_imports_count_for_bbox(self, bbox: Bbox):
        return (
            self.__filter_city(self.session.query(City.import_date, func.count(".*").label("count")))
            .filter(Boundary.insee == City.insee)
            .filter(Boundary.geometry.ST_DWithin(self.__build_srid(bbox), bbox.max_distance()))
            .group_by(City.import_date)
            .all()
        )

    def get_cities_for_year(self, date):
        return self.session.query(City.name, City.insee).filter(City.import_date == date).order_by(City.name).all()

    def get_cities_for_bbox(self, bbox: Bbox):
        # we should fetch all cities within the view but at least 110km radius around
        distance = min(bbox.max_distance(), 1.0)
        return (
            self.__filter_city(self.session.query(City))
            .filter(Boundary.insee == City.insee)
            .filter(func.ST_DWithin(Boundary.geometry, self.__build_srid(bbox), distance))
            .order_by(func.ST_Distance(self.__build_srid(bbox), Boundary.geometry))
            .all()
        )

    def get_departments(self):
        # admin_level 6 are departments, however some are handled differently by OSM and cadastre.
        # for instance, 69 (Rhône) exists as 69D and 60M in OSM at level 6, so we also take level 5
        return self.__flat(
            self.session.query(Boundary.insee)
            .filter(Boundary.admin_level.in_([5, 6]))
            .filter(Boundary.insee != "")
            .order_by(Boundary.insee)
            .all()
        )

    def get_department(self, insee):
        return (
            self.session.query(Boundary)
            .filter(Boundary.admin_level.in_([5, 6]))
            .filter(Boundary.insee == insee)
            .first()
        )

    def get_department_import_stats(self, insee):
        return (
            self.session.query(City.import_date, func.count("*"))
            .filter(City.department == str(insee))
            .group_by(City.import_date)
            .order_by(City.import_date)
            .all()
        )

    def get_department_simplified_buildings(self, insee):
        return self.__flat(
            self.session.query(City.import_details["simplified"])
            .filter(City.department == str(insee))
            .filter(func.json_array_length(City.import_details["simplified"]) != 0)
            .all()
        )

    def get_departments_for_bbox(self, bbox: Bbox):
        return self.__flat(
            self.session.query(Boundary.insee.distinct())
            .filter(Boundary.admin_level.in_([5, 6]))
            .filter((Boundary.insee != "") is not False)
            .filter(Boundary.geometry.intersects(func.ST_MakeEnvelope(*bbox.coords)))
            .order_by(Boundary.insee)
            .all()
        )

    def get_city_geometry(self, insee):
        return self.__filter_city(self.session.query(Boundary.geometry.ST_AsGeoJSON()), insee).filter(Boundary.insee == City.insee).first()

    def get_unknown_cities(self, departments) -> [City]:
        return (
            self.session.query(City)
            .filter(City.department.in_([x.zfill(2) for x in departments]))
            .filter(City.import_date == "unknown")
            .order_by(City.insee)
            .all()
        )

    def get_obsolete_city(self, ignored):
        """
            Find the city that has the most urging need of import (never > unknown > old import > raster).
            Also privileges ready-to-work cities (cadastre data available) upon the others.
            However we do NOT want this to be a fixed-order list (to avoid multiple users working on the
            same city), so we finally randomize final list of matching cities.
        """
        past_month = datetime.now() - timedelta(days=30)
        return (
            self.session.query(City, Boundary.geometry.ST_Centroid().ST_AsText().label("position"),)
            .filter(Boundary.insee == City.insee)
            .order_by(City.import_date.in_(ignored))
            .order_by(City.import_date != "never")
            .order_by(City.import_date != "unfinished")
            .order_by(City.import_date != "unknown")
            .order_by(City.import_date != "raster")
            .order_by(City.import_date != "date")
            .order_by(City.import_date < str(past_month))
            .order_by(func.random())
            .limit(1)
            .first()
        )

    def get_raster_cities_count(self, department):
        return self.session.query(func.count("*")).filter(City.department == department.zfill(2)).filter(City.is_raster).scalar()

    def get_building_dates_per_city_for_insee(self, insee, ignored_buildings):
        return (
            self.__filter_city(
                self.session.query(
                    City.insee,
                    City.name,
                    func.concat(Building.source, Building.source_date).label("dated_source"),
                    func.count("*"),
                    City.is_raster,
                )
            )
            .filter(City.insee.startswith(insee.zfill(2)))
            .filter(City.insee == Boundary.insee)
            .filter(Building.building != None)
            .filter(Building.building.notin_(ignored_buildings))
            .filter(Building.geometry.ST_GeometryType() != "ST_Point")
            .filter(Boundary.geometry.ST_Contains(Building.geometry))
            .group_by(City.insee, City.name, "dated_source", City.is_raster)
            .all()
        )

    def get_point_buildings_per_city_for_insee(self, insee):
        GeoCities = (
            self.__filter_city(self.session.query(Boundary.insee, Boundary.name, City.is_raster, Boundary.geometry))
            .filter(Boundary.admin_level >= 8)
            .filter(City.insee == Boundary.insee)
            .filter(City.insee.startswith(insee.zfill(2)))
            .filter(City.is_raster == False)
            .subquery(name="GeoCities")
        )

        return (
            self.session.query(GeoCities.c.insee, Building.osm_id)
            .filter(Building.building != None)
            .filter(Building.geometry.ST_GeometryType() == "ST_Point")
            .filter(GeoCities.c.geometry.ST_Contains(Building.geometry))
            .order_by(GeoCities.c.insee)
            .all()
        )
