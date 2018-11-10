#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from math import sqrt

import psycopg2
import psycopg2.extras
import logging
from geojson import Feature, FeatureCollection, loads
import re
import operator
from collections import defaultdict

from batimap.bbox import Bbox
from citydto import CityDTO

LOG = logging.getLogger(__name__)


class Postgis(object):

    def __init__(self, db, user, passw, port, host, tileserver):
        self.db = db
        self.user = user
        self.passw = passw
        self.port = port
        self.host = host
        self.tileserver = tileserver

    def execute(self, req, args=None):
        try:
            self.cursor.execute(req, args)
        except Exception as e:
            LOG.warning(f"Could not execute request, will retry due to: {e}")
            self.connection = psycopg2.connect(
                database=self.db, user=self.user, password=self.passw, port=self.port, host=self.host)
            self.cursor = self.connection.cursor()
            self.cursor.execute(req, args)

    def create_tables(self):
        req = """
                CREATE TABLE IF NOT EXISTS
                    city_stats(
                        insee VARCHAR(10) PRIMARY KEY NOT NULL,
                        department VARCHAR(3) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        name_cadastre VARCHAR(100) UNIQUE NOT NULL,
                        is_raster BOOLEAN,
                        date VARCHAR(10),
                        last_update TIMESTAMP,
                        details TEXT,
                        date_cadastre TIMESTAMP
                    )
        """
        self.execute(req)
        LOG.debug('city_stats table created')

        # self.execute("CREATE INDEX IF NOT EXISTS way_gist ON planet_osm_polygon USING gist(way);")
        # self.execute("CREATE INDEX IF NOT EXISTS insee_idx ON planet_osm_polygon((\"ref:INSEE\"));")
        self.connection.commit()

    def get_insee(self, insee: int) -> FeatureCollection:
        req = """
                SELECT
                    p.name,
                    c.insee,
                    c.date,
                    ST_AsGeoJSON(p.geometry) AS geometry
                FROM
                    osm_admin  p,
                    city_stats c
                WHERE
                    p.insee = %s
                    AND p.insee = c.insee
        """
        self.execute(req, [insee])
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
                    p.name,
                    c.insee
                FROM
                    osm_admin  p,
                    city_stats c
                WHERE
                    p.admin_level::int >= 8
                    AND c.insee = p.insee
                    AND c.date = %s
                """
        self.execute(req, [date])

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_dates_count(self):
        req = """
                SELECT
                    date,
                    count(*)
                FROM
                    city_stats
                GROUP BY
                    date
        """
        self.execute(req)

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_cities_in_bbox(self, lonNW: float, latNW: float, lonSE: float, latSE: float):

        req = """
                SELECT
                    p.name,
                    c.insee,
                    c.date,
                    c.details,
                    c.date_cadastre
                FROM
                    osm_admin  p,
                    city_stats c
                WHERE
                    p.admin_level::int >= 8
                    AND c.insee = p.insee
                    AND ST_DWithin(p.geometry, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), %(distance)s)
                ORDER BY
                    ST_Distance(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), p.geometry)
               """

        # we should fetch all cities within the view
        maxDistance = sqrt((lonNW - lonSE)**2 + (latNW - latSE)**2) / 2
        # instead if we zoomed out too much, we limit to maximum 110km
        # radius circle
        maxDistance = min(1., maxDistance)

        args = {
            'distance': maxDistance,
            'lon': (lonNW + lonSE) / 2.,
            'lat': (latNW + latSE) / 2.,
        }
        self.execute(req, args)

        results = []
        for row in self.cursor.fetchall():
            results.append(CityDTO(
                row[0],
                row[1],
                row[2],
                row[3],
                row[4] is not None)
            )
        return results

    def get_legend_in_bbox(self, lonNW: float, latNW: float, lonSE: float, latSE: float):

        req = """
                SELECT
                    c.date,
                    count(c.date)
                FROM
                    osm_admin  p,
                    city_stats c
                WHERE
                    p.admin_level::int >= 8
                    AND c.insee = p.insee
                    AND ST_DWithin(p.geometry, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), %(distance)s)
                GROUP BY
                    c.date
               """

        # we should fetch all cities within the view
        maxDistance = sqrt((lonNW - lonSE)**2 + (latNW - latSE)**2) / 2

        args = {
            'distance': maxDistance,
            'lon': (lonNW + lonSE) / 2.,
            'lat': (latNW + latSE) / 2.,
        }
        self.execute(req, args)

        results = []
        total = 0
        for row in self.cursor.fetchall():
            if row[1] > 0:
                results.append({
                    'name': row[0],
                    'count': row[1],
                })
                total += row[1]
        for r in results:
            r["percent"] = round(r["count"] * 100.0 / total, 2)

        return results

    def get_departments(self):
        req = """
            SELECT
                DISTINCT(SUBSTR(p.insee, 1, CHAR_LENGTH(p.insee) - 3)) as dept
            FROM
                osm_admin p
            WHERE
                p.admin_level::int >= 7
                AND p.insee is not null
                AND CHAR_LENGTH(p.insee) >= 3
            ORDER BY dept
        """
        self.execute(req)

        return [x[0] for x in self.cursor.fetchall()]

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
        self.execute(req, [department])

        return sorted([x[0].strip() for x in self.cursor.fetchall()])

    def name_for_insee(self, insee):
        req = """
                SELECT DISTINCT
                    name
                FROM
                    osm_admin  p
                WHERE
                    p.insee = %s
                    AND p.admin_level::int >= 8
                    AND p.boundary = 'administrative'
        """
        self.execute(req, [insee])

        results = self.cursor.fetchall()
        if len(results) == 0:
            LOG.error("Cannot found city with INSEE {}.".format(insee))
            return None

        return results[0][0] if len(results) else None

    def insee_for_name(self, name, interactive=True):
        req = """
                SELECT
                    insee,
                    name
                FROM
                    city_stats
                WHERE
                    name ILIKE %s || '%%'
                OR
                    name_cadastre ILIKE %s || '%%'
        """
        self.execute(req, [name, name])

        results = [x for x in self.cursor.fetchall()]
        if len(results) == 0:
            LOG.error("Cannot found city with name {}.".format(name))
            return None
        elif len(results) == 1:
            return results[0][0]
        elif len(results) > 30:
            LOG.error(
                "Too many cities name starting with {} (total: {}). Please check name.".format(name, len(results)))
            return None
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
            LOG.error("More than one city with name {}.".format(name))
            return None

    def last_import_date(self, insee):
        req = """
                SELECT
                    date
                FROM
                    city_stats
                WHERE
                    insee = %s
        """
        self.execute(req, [insee])

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
        self.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)
        return results[0] if len(results) else None

    def within_department(self, department: str):
        department = department.zfill(2)
        req = """
                SELECT DISTINCT
                    p.insee as insee
                FROM
                    osm_admin  p,
                    city_stats c
                WHERE
                    p.insee = c.insee
                    AND p.admin_level::int >= 8
                    AND p.boundary='administrative'
                    AND p.insee LIKE %s || '%%'
                ORDER BY
                    insee
        """
        self.execute(req, [department])

        return [x[0] for x in self.cursor.fetchall()]

    def bbox_for_insee(self, insee):
        req = """
                SELECT
                    Box2D(p.geometry)
                FROM
                    osm_admin  p
                WHERE
                    p.insee = %s
                    AND p.admin_level::int >= 8
                    AND p.boundary = 'administrative'
        """
        self.execute(req, [insee])

        results = self.cursor.fetchall()
        if len(results) > 1:
            # fixme: this may happen for multi polygons cities (76218 - Doudeauville for instance)
            LOG.warning(f"Expected a single bbox for insee {insee} at most, "
                        f"but found {len(results)} instead. Taking the first one.")

        return Bbox(results[0][0]) if len(results) else None

    def update_stats_for_insee(self, tuples):
        req = """
                UPDATE city_stats as c
                SET date = e.date, name = e.name, last_update = now(), details = e.details
                FROM (VALUES %s) as e(insee, name, date, details)
                WHERE e.insee = c.insee
        """

        try:
            psycopg2.extras.execute_values(self.cursor, req, tuples)
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))

    def insert_stats_for_insee(self, tuples):
        req = """
                INSERT INTO city_stats(insee, department, name, name_cadastre, is_raster, date)
                VALUES %s
                ON CONFLICT (insee) DO
                UPDATE SET
                    department = excluded.department,
                    name_cadastre = excluded.name_cadastre,
                    is_raster = excluded.is_raster,
                    date = excluded.date
        """
        try:
            psycopg2.extras.execute_values(
                self.cursor, req, tuples)
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))

    def upsert_city_status(self, tuples):
        req = """
                UPDATE city_stats as c
                SET date_cadastre = e.date_cadastre
                FROM (VALUES %s) as e(name_cadastre, date_cadastre)
                WHERE e.name_cadastre = c.name_cadastre
        """
        try:
            LOG.debug(f"Updating cities date_cadastre for {tuples}")
            psycopg2.extras.execute_values(
                self.cursor, req, tuples)
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))

    def fetch_buildings_stats(self, table, department, buildings_count, insee_name):
            query = f"""
                WITH cities AS (
                    SELECT
                        p.insee,
                        p.name,
                        p.geometry,
                        c.is_raster
                    FROM
                        osm_admin  p,
                        city_stats c
                    WHERE
                        p.insee like %s || '%%'
                        AND p.admin_level::int >= 8
                        AND p.insee = c.insee
                )
                SELECT
                    c.insee,
                    c.name,
                    p.source,
                    count(p.*),
                    c.is_raster
                FROM
                    cities c,
                    {table} p
                WHERE
                    p.building is not null
                    AND ST_Intersects(c.geometry, p.geometry)
                GROUP BY
                    c.insee, c.name, p.source, c.is_raster
                ORDER BY
                    c.insee
            """

            self.execute(query, [department.zfill(2)])

            cadastre_src2date_regex = re.compile(r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')
            for (insee, name, source, count, is_raster) in self.cursor.fetchall():
                if is_raster:
                    insee_name[insee] = name
                    buildings_count[insee] = {}
                    buildings_count[insee]['raster'] = 1
                    continue

                date = re.sub(cadastre_src2date_regex, r'\2', (source or 'unknown').lower())
                if not buildings_count.get(insee):
                    buildings_count[insee] = defaultdict(lambda: 0, {})
                insee_name[insee] = name
                buildings_count[insee][date] += count

    def import_city_stats_from_osmplanet(self, departments):
        LOG.info(f"Import buildings from db for departments {departments}…")
        for department in departments:
            LOG.info(f"Import buildings from db for department {department}…")

            buildings_count = {}
            insee_name = {}

            # for table in ['polygon', 'point', 'line']:
            self.fetch_buildings_stats(f'osm_buildings', department, buildings_count, insee_name)

            tuples = []
            for insee, counts in buildings_count.items():
                date_match = re.compile(r'^(\d{4}|raster)$').match(max(counts.items(), key=operator.itemgetter(1))[0])
                date = date_match.groups()[0] if date_match and date_match.groups() else 'unknown'
                tuples.append((insee, insee_name[insee], date, json.dumps({'dates': counts})))
            self.update_stats_for_insee(tuples)
