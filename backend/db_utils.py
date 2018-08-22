#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from math import cos, floor, log, pi, radians, sqrt, tan

import grequests
import psycopg2
import logging
from geojson import Feature, FeatureCollection, loads

from batimap.bbox import Bbox

LOG = logging.getLogger(__name__)


class Postgis(object):

    def __init__(self, db, user, passw, port, host, tileserver):
        self.connection = psycopg2.connect(
            database=db, user=user, password=passw, port=port, host=host)
        self.cursor = self.connection.cursor()
        self.tileserver = tileserver

    def create_tables(self):
        req = """
                CREATE TABLE IF NOT EXISTS
                    city_stats(
                        insee VARCHAR(10) PRIMARY KEY NOT NULL,
                        department VARCHAR(3) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        name_cadastre VARCHAR(100) NOT NULL,
                        is_raster BOOLEAN,
                        date VARCHAR(10),
                        last_update TIMESTAMP,
                        details TEXT
                    )
        """
        self.cursor.execute(req)
        LOG.debug('city_stats table created')
        req = """
                CREATE INDEX IF NOT EXISTS
                    insee_idx
                ON
                    planet_osm_polygon ((tags->'ref:INSEE'));
        """
        self.cursor.execute(req)
        LOG.debug('insee_idx index created')
        self.connection.commit()

    def get_insee(self, insee: int) -> FeatureCollection:
        req = """
                SELECT
                    p.name,
                    c.insee,
                    c.date,
                    ST_AsGeoJSON(p.way) AS geometry
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.tags->'ref:INSEE' = %s
                AND
                    p.tags->'ref:INSEE' = c.insee
        """
        self.cursor.execute(req, [insee])
        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                'name': "{} - {}".format(row[0], row[1]),
                'date': row[2]
            },
                geometry=loads(row[3])))

        return FeatureCollection(features)

    def get_cities_for_date(self, date):
        req = """
                SELECT
                    p.name, c.insee
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.tags->'admin_level' = '8'
                AND
                    c.insee = p.tags->'ref:INSEE'
                AND
                    c.date = %s
                """
        self.cursor.execute(req, [date])

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_colors(self):
        req = """
                SELECT
                    date,
                    count(*)
                FROM
                    city_stats
                GROUP BY
                    date
        """
        self.cursor.execute(req)

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_city_with_colors(self, dates, lonNW: float, latNW: float, lonSE: float, latSE: float) -> FeatureCollection:
        req = """
                SELECT
                    count(p.name)
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.tags->'admin_level' = '8'
                AND
                    c.insee = p.tags->'ref:INSEE'
                AND
                    c.date in (%s)
                """
        self.cursor.execute(req, ["','".join(dates)])
        count = self.cursor.fetchall()[0][0]

        req = """
                SELECT
                    p.name,
                    c.insee,
                    c.date,
                    ST_AsGeoJSON(p.way, 6) AS geometry
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.tags->'admin_level' = '8'
                AND
                    c.insee = p.tags->'ref:INSEE'
                AND
                    c.date in (%(date)s)
               """
        args = {'date': "','".join(dates)}

        # if there are too much cities, filter by distance
        if len(dates) > 1 and count > 1500:
            # we should fetch all cities within the view
            maxDistance = sqrt((lonNW - lonSE)**2 + (latNW - latSE)**2)
            # instead if we zoomed out too much, we limit to maximum 110km
            # radius circle
            maxDistance = min(1., maxDistance)

            req += """
                AND
                    ST_DWithin(way, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326),
                    %(distance)s)
                ORDER BY
                    ST_Distance(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), p.way)
            """
            args.update({
                'lon': (lonNW + lonSE) / 2.,
                'lat': (latNW + latSE) / 2.,
                'distance': maxDistance,
            })

        self.cursor.execute(req, args)

        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                'name': "{} - {}".format(row[0], row[1]),
                'date': row[2]
            },
                geometry=loads(row[3])))

        return FeatureCollection(features)

    def get_department_colors(self, department):
        req = """
            SELECT
                date
            FROM
                city_stats
            WHERE
                department = %s
            GROUP BY
                date
            ORDER BY
                count(*) DESC
        """
        self.cursor.execute(req, [department])

        return sorted([x[0].strip() for x in self.cursor.fetchall()])

    def deg_to_xy(self, lat, lon, zoom):
        x = int(floor((lon + 180) / 360 * (1 << zoom)))
        y = int(floor(
            (1 - log(tan(radians(lat)) + 1 / cos(radians(lat))) / pi) / 2 * (1 << zoom)))
        return (x, y)

    def clear_tiles(self, insee):
        req = """
            SELECT
                ST_AsGeoJSON(ST_EXTENT(way))
            FROM
                planet_osm_polygon
            WHERE
                tags->'ref:INSEE' = %s
        """
        self.cursor.execute(req, [insee])
        coords = json.loads(self.cursor.fetchall()[0][0])['coordinates'][0]
        (lon1, lat1) = coords[0]
        (lon2, lat2) = coords[2]
        for z in range(3, 14):
            (x1, y1) = self.deg_to_xy(lat1, lon1, z)
            (x2, y2) = self.deg_to_xy(lat2, lon2, z)
            urls = []
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    url = "/{}/{}/{}.vector.pbf".format(
                        self.tileserver, z, x, y)
                    urls.append(url)
            rs = (grequests.request('PURGE', x) for x in urls)
            grequests.map(rs)

    def name_for_insee(self, insee, ignore_error=False):
        req = """
                SELECT DISTINCT
                    name
                FROM
                    planet_osm_polygon
                WHERE
                    tags->'ref:INSEE' = %s
                AND
                    admin_level = '8'
                AND
                    boundary = 'administrative'
        """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()

        if len(results) == 0 and not ignore_error:
            LOG.critical("Cannot found city with INSEE {}.".format(insee))
            exit(1)

        return results[0][0] if len(results) else None

    def insee_for_name(self, name, interactive=True):
        req = """
                SELECT
                    tags->'ref:INSEE',
                    name
                FROM
                    planet_osm_polygon
                WHERE
                    admin_level = '8'
                AND
                    boundary = 'administrative'
                AND
                    name ILIKE %s || '%%'
        """
        self.cursor.execute(req, [name])

        results = [x for x in self.cursor.fetchall()]
        if len(results) == 0:
            LOG.critical("Cannot found city with name {}.".format(name))
            exit(1)
        elif len(results) == 1:
            return results[0][0]
        elif len(results) > 30:
            LOG.critical(
                "Too many cities name starting with {} (total: {}). Please check name.".format(name, len(results)))
            exit(1)
        elif interactive:
            user_input = ''
            while user_input not in [x[0] for x in results]:
                user_input = input(
                    "More than one city found. Please enter your desired one from the following list:\n\t{}\n".format(
                        '\n\t'.join(
                            ['{} - {}'.format(x[0], x[1]) for x in results]
                        )
                    )
                )
            return user_input
        else:
            LOG.critical("More than one city with name {}.".format(name))
            exit(1)

    def last_import_date(self, insee):
        req = """
                SELECT
                    date
                FROM
                    city_stats
                WHERE
                    insee = %s
        """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)
        return results[0][0] if len(results) else None

    def city_data(self, insee, data_queries):
        if not data_queries:
            data_queries = ["*"]
        req = f"""
                SELECT
                    {", ".join(data_queries)}
                FROM
                    city_stats
                WHERE
                    insee = %s
        """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)
        return results[0] if len(results) else None

    def within_department(self, department: str):
        department = '{:0>2}%'.format(department)
        req = """
                SELECT DISTINCT
                    tags->'ref:INSEE' AS insee
                FROM
                    planet_osm_polygon
                WHERE
                    admin_level='8'
                AND
                    boundary='administrative'
                AND
                    tags->'ref:INSEE' LIKE %s
                ORDER BY
                    insee
        """
        self.cursor.execute(req, [department])

        return [x[0] for x in self.cursor.fetchall()]

    def bbox_for_insee(self, insee):
        req = """
                SELECT
                    Box2D(way)
                FROM
                    planet_osm_polygon
                WHERE
                    tags->'ref:INSEE' = %s
                AND
                    admin_level = '8'
                AND
                    boundary = 'administrative'
        """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        if len(results) > 1:
            # fixme: this may happen for multi polygons cities (76218 - Doudeauville for instance)
            LOG.critical(f"Expected a single result at most but found {len(results)}")

        return Bbox(results[0][0]) if len(results) else None

    def update_stats_for_insee(self, insee, date, details, update_time=False):
        req = """
                UPDATE
                    city_stats
                SET date = %s, last_update = now(), details = %s
                WHERE insee = %s
        """

        try:
            self.cursor.execute(
                req, [date, details, insee])
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))

    def insert_stats_for_insee(self, insee, dept, nom_commune, is_raster):
        name = self.name_for_insee(insee, True)
        LOG.debug(f"Inserting stats for {insee} {nom_commune} - {name}")
        if not name:
            LOG.warning(f"Cannot find city with insee {insee}, did you import OSM data for this department?")
            name = ''

        req = """
                INSERT INTO
                    city_stats(insee, department, name, name_cadastre, is_raster)
                VALUES
                    (%s, %s, %s, %s, %s)
                ON CONFLICT (insee)
                DO
                UPDATE SET
                    department = excluded.department,
                    name_cadastre = excluded.name_cadastre,
                    is_raster = excluded.is_raster
        """
        try:
            self.cursor.execute(
                req, [insee, dept, name, nom_commune, is_raster])
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))
