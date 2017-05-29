import psycopg2
import json

from geojson import Feature, FeatureCollection, loads


class Postgis(object):
    def __init__(self, db, user, passw, port, host):
        self.connection = psycopg2.connect(database=db, user=user, password=passw, port=port, host=host)
        self.cursor = self.connection.cursor()

    def get_insee(self, insee: int) -> FeatureCollection:
        self.cursor.execute((""
                            "        SELECT p.name, c.insee, c.color, ST_AsGeoJSON(p.way) AS geometry\n"
                            "        FROM planet_osm_polygon p, color_city c\n"
                            "        WHERE p.tags->'ref:INSEE' = '{}'\n"
                            "        AND p.tags->'ref:INSEE' = c.insee\n"
                            "").format(insee))

        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                                                'name': "{} - {}".format(row[0], row[1]),
                                                'color': row[2]
                                                },
                                    geometry=loads(row[3])))

        return FeatureCollection(features)

    def get_colors(self):
        self.cursor.execute((""
                            "        SELECT DISTINCT color\n"
                            "        FROM color_city\n"
                            ""))
        features = []

        return sorted([x[0].strip() for x in self.cursor.fetchall()])

    def get_city_with_colors(self, colors, lonNW: float, latNW: float, lonSE: float, latSE: float) -> FeatureCollection:
        self.cursor.execute((""
                            "        SELECT p.name, c.insee, c.color, ST_AsGeoJSON(p.way) AS geometry\n"
                            "        FROM planet_osm_polygon p, color_city c\n"
                            "        WHERE ST_Intersects(ST_SetSRID(ST_MAKEBox2D(ST_MakePoint({}, {}), ST_MakePoint({}, {})),4326), p.way)\n"
                            "        AND p.tags->'admin_level' = '8'\n"
                            "        AND c.insee = p.tags->'ref:INSEE'\n"
                            "        AND c.color in ('{}')\n"
                            "        ORDER BY ST_Distance(ST_SetSRID(ST_MakePoint({}, {}),4326), p.way)\n"
                            "        LIMIT 300\n"
                            "").format(lonNW, latNW, lonSE, latSE, "','".join(colors), (lonNW + lonSE) / 2., (latNW + latSE) / 2.))

        features = []

        for row in self.cursor.fetchall():
            features.append(Feature(properties={
                                                'name': "{} - {}".format(row[0], row[1]),
                                                'color': row[2]
                                                },
                                    geometry=loads(row[3])))

        return FeatureCollection(features)
