import json
from math import cos, floor, log, pi, radians, sqrt, tan

import psycopg2
from geojson import Feature, FeatureCollection, loads

import grequests

from batimap.bbox import Bbox


class Postgis(object):

    def __init__(self, db, user, passw, port, host):
        self.connection = psycopg2.connect(
            database=db, user=user, password=passw, port=port, host=host)
        self.cursor = self.connection.cursor()

    def get_insee(self, insee: int) -> FeatureCollection:
        req = ((""
                "        SELECT p.name, c.insee, c.color, ST_AsGeoJSON(p.way) AS geometry\n"
                "        FROM planet_osm_polygon p, color_city c\n"
                "        WHERE p.tags->'ref:INSEE' = '{}'\n"
                "        AND p.tags->'ref:INSEE' = c.insee\n"
                "").format(insee))
        self.cursor.execute(req)
        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                'name': "{} - {}".format(row[0], row[1]),
                'color': row[2]
            },
                geometry=loads(row[3])))

        return FeatureCollection(features)

    def get_colors(self):
        req = ((""
                "        SELECT color, count(*)\n"
                "        FROM color_city\n"
                "        GROUP BY color\n"
                ""))
        self.cursor.execute(req)

        return sorted([[x[0].strip(), x[1]] for x in self.cursor.fetchall()])

    def get_city_with_colors(self, colors, lonNW: float, latNW: float, lonSE: float, latSE: float) -> FeatureCollection:
        req = ((""
                "        SELECT count(p.name)\n"
                "        FROM planet_osm_polygon p, color_city c\n"
                "        WHERE p.tags->'admin_level' = '8'\n"
                "        AND c.insee = p.tags->'ref:INSEE'\n"
                "        AND c.color in ('{colors}')\n"
                "").format(colors="','".join(colors)))
        self.cursor.execute(req)
        count = self.cursor.fetchall()[0][0]

        req = (""
               "        SELECT p.name, c.insee, c.color, ST_AsGeoJSON(p.way, 6) AS geometry\n"
               "        FROM planet_osm_polygon p, color_city c\n"
               "        WHERE p.tags->'admin_level' = '8'\n"
               "        AND c.insee = p.tags->'ref:INSEE'\n"
               "        AND c.color in ('{colors}')\n"
               "").format(colors="','".join(colors))

        # if there are too much cities, filter by distance
        if len(colors) > 1 and count > 1500:
            # we should fetch all cities within the view
            maxDistance = sqrt((lonNW - lonSE)**2 + (latNW - latSE)**2)
            # instead if we zoomed out too much, we limit to maximum 110km
            # radius circle
            maxDistance = min(1., maxDistance)

            req += ((""
                     "        AND ST_DWithin(way, ST_SetSRID(ST_MakePoint({lon}, {lat}),4326), {distance})\n"
                     "        ORDER BY ST_Distance(ST_SetSRID(ST_MakePoint({lon}, {lat}),4326), p.way)\n"
                     "").format(lon=(lonNW + lonSE) / 2., lat=(latNW + latSE) / 2., distance=maxDistance))

        self.cursor.execute(req)

        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                'name': "{} - {}".format(row[0], row[1]),
                'color': row[2]
            },
                geometry=loads(row[3])))

        return FeatureCollection(features)

    def get_department_colors(self, department):
        req = ((""
                "        SELECT color\n"
                "        FROM color_city\n"
                "        WHERE department = '{}'\n"
                "        GROUP BY color\n"
                "        ORDER BY count(*) DESC\n"
                "").format(department))
        self.cursor.execute(req)

        return sorted([x[0].strip() for x in self.cursor.fetchall()])

    def deg_to_xy(self, lat, lon, zoom):
        x = int(floor((lon + 180) / 360 * (1 << zoom)))
        y = int(floor(
            (1 - log(tan(radians(lat)) + 1 / cos(radians(lat))) / pi) / 2 * (1 << zoom)))
        return (x, y)

    def clear_tiles(self, insee):
        req = ((""
                "        SELECT ST_AsGeoJSON(ST_EXTENT(way))\n"
                "        FROM planet_osm_polygon\n"
                "        WHERE tags->'ref:INSEE' = '{}'\n"
                "").format(insee))
        self.cursor.execute(req)
        coords = json.loads(self.cursor.fetchall()[0][0])['coordinates'][0]
        (lon1, lat1) = coords[0]
        (lon2, lat2) = coords[2]
        for z in range(3, 14):
            (x1, y1) = self.deg_to_xy(lat1, lon1, z)
            (x2, y2) = self.deg_to_xy(lat2, lon2, z)
            urls = []
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    url = "https://cadastre.damsy.net/tegola/maps/bati/{}/{}/{}.vector.pbf".format(
                        z, x, y)
                    urls.append(url)
            rs = (grequests.request('PURGE', x) for x in urls)
            grequests.map(rs)

    def name_for_insee(self, insee):
        req = """
                        SELECT DISTINCT name
                        FROM planet_osm_polygon
                        WHERE tags->'ref:INSEE' = %s
                        AND admin_level = '8'
                        AND boundary = 'administrative'
              """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()

        if len(results) == 0:
            self.log.critical("Cannot found city with INSEE {}.".format(insee))
            exit(1)

        return results[0][0] if len(results) else None

    def insee_for_name(self, name, interactive=True):
        req = """
                        SELECT tags->'ref:INSEE', name
                        FROM planet_osm_polygon
                        WHERE admin_level = '8'
                        AND boundary = 'administrative'
                        AND name ILIKE %s || '%%'
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

    def last_import_color(self, insee):
        req = """
                        SELECT TRIM(color)
                        FROM color_city
                        WHERE insee = %s
              """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)
        return results[0][0] if len(results) else None

    def last_import_author(self, insee):
        req = """
                        SELECT last_author
                        FROM color_city
                        WHERE insee = %s
                """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)
        return results[0][0] if len(results) else None

    def within_departments(self, departments):
        req = """
                        SELECT DISTINCT tags->'ref:INSEE' AS insee
                        FROM planet_osm_polygon
                        WHERE admin_level='8'
                        AND boundary='administrative'
                        AND tags->'ref:INSEE' LIKE ANY(%s)
                        ORDER BY insee
                """
        self.cursor.execute(req, ([x + "%" for x in departments], ))

        return [x[0] for x in self.cursor.fetchall()]

    def bbox_for_insee(self, insee):
        req = """
                        SELECT Box2D(way)
                        FROM planet_osm_polygon
                        WHERE tags->'ref:INSEE' = %s
                        AND admin_level = '8'
                        AND boundary = 'administrative'
                """
        self.cursor.execute(req, [insee])

        results = self.cursor.fetchall()
        assert(len(results) <= 1)

        return Bbox(results[0][0]) if len(results) else None

    def update_stats_for_insee(self, insee, color, department, author, update_time=False):
        req = """
                        INSERT INTO color_city
                        VALUES (%s, %s,
                                %s, now(), %s)
                        ON CONFLICT (insee) DO UPDATE SET color = excluded.color, department = excluded.department
                """
        if update_time:
            req += ", last_update = excluded.last_update, last_author = excluded.last_author"
        try:
            self.cursor.execute(req, [insee, department, color, author])
            self.connection.commit()
        except Exception as e:
            LOG.warning("Cannot write in database: " + str(e))
            pass
