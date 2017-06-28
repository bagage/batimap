import psycopg2

from geojson import Feature, FeatureCollection, loads
from math import sqrt, floor, tan, log, cos, pi, radians
import json
import grequests


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
                    url = "https://overpass.damsy.net/tegola/maps/bati/{}/{}/{}.vector.pbf".format(
                        z, x, y)
                    urls.append(url)
            rs = (grequests.request('PURGE', x) for x in urls)
            grequests.map(rs)
