#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from math import cos, floor, log, pi, radians, tan, sqrt

import grequests
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

        self.cursor.execute("CREATE INDEX IF NOT EXISTS way_gist ON planet_osm_polygon USING gist(way);")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS insee_idx ON planet_osm_polygon((\"ref:INSEE\"));")
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
                    p."ref:INSEE" = %s
                AND
                    p."ref:INSEE" = c.insee
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
                    p.'admin_level' = '8'
                AND
                    c.insee = p."ref:INSEE"
                AND
                    c.date = %s
                """
        self.cursor.execute(req, [date])

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
        self.cursor.execute(req)

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_cities_in_bbox(self, lonNW: float, latNW: float, lonSE: float, latSE: float):

        req = """
                SELECT
                    p.name,
                    c.insee,
                    c.date,
                    c.details
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.admin_level = '8'
                AND
                    c.insee = p."ref:INSEE"
                AND
                    ST_DWithin(way, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), %(distance)s)
                ORDER BY
                    ST_Distance(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), p.way)
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
        self.cursor.execute(req, args)

        results = []
        for row in self.cursor.fetchall():
            results.append(CityDTO(
                row[0],
                row[1],
                row[2],
                row[3])
            )
        return results

    def get_legend_in_bbox(self, lonNW: float, latNW: float, lonSE: float, latSE: float):

        req = """
                SELECT
                    c.date,
                    count(c.date)
                FROM
                    planet_osm_polygon p,
                    city_stats c
                WHERE
                    p.admin_level = '8'
                AND
                    c.insee = p."ref:INSEE"
                AND
                    ST_DWithin(way, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s),4326), %(distance)s)
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
        self.cursor.execute(req, args)

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
                "ref:INSEE"
            FROM
                planet_osm_polygon
            WHERE
                admin_level = '6'
            ORDER BY
                "ref:INSEE"
        """
        self.cursor.execute(req)

        # erase non digit characters, eg Lyon (69D) should be considered as department 69
        depts = [''.join(y for y in x[0] if y.isdigit()) for x in self.cursor.fetchall()]
        # avoid duplicates
        return [x for i, x in enumerate(depts) if depts.index(x) == i]

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
                "ref:INSEE" = %s
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
                    "ref:INSEE" = %s
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
                    "ref:INSEE",
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
        department = department.zfill(2)
        req = """
                SELECT DISTINCT
                    "ref:INSEE" AS insee
                FROM
                    planet_osm_polygon
                WHERE
                    admin_level='8'
                AND
                    boundary='administrative'
                AND
                    "ref:INSEE" LIKE %s || '%%'
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
                    "ref:INSEE" = %s
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

    def fetch_buildings_stats(self, table, department, buildings_count, insee_name):
            query = f"""
                with cities as (
                    select insee, p.name, way, is_raster
                    from planet_osm_polygon p, city_stats
                    where "ref:INSEE" like %s || '%%'
                    and admin_level = '8'
                    and "ref:INSEE" = insee
                )
                select c.insee, c.name, p.source, count(p.*), c.is_raster
                from cities c, {table} p
                where p.building is not null and ST_Contains(c.way, p.way)
                group by c.insee, c.name, p.source, c.is_raster
                order by insee
            """
            # fixme: search in planet_osm_point and planet_osm_line too!

            self.cursor.execute(query, [department.zfill(2)])

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

            for table in ['polygon', 'point', 'line']:
                self.fetch_buildings_stats(f'buildings_osm_{table}', department, buildings_count, insee_name)

            tuples = []
            for insee, counts in buildings_count.items():
                date_match = re.compile(r'^(\d{4}|raster)$').match(max(counts.items(), key=operator.itemgetter(1))[0])
                date = date_match.groups()[0] if date_match and date_match.groups() else 'unknown'
                tuples.append((insee, insee_name[insee], date, json.dumps({'dates': counts})))
            self.update_stats_for_insee(tuples)
