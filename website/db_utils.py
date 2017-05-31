import psycopg2
import json

from geojson import Feature, FeatureCollection, loads
from math import sqrt

class Postgis(object):
    def __init__(self, db, user, passw, port, host):
        self.connection = psycopg2.connect(database=db, user=user, password=passw, port=port, host=host)
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
                            "        SELECT DISTINCT color\n"
                            "        FROM color_city\n"
                            ""))
        self.cursor.execute(req)
        features = []

        return sorted([x[0].strip() for x in self.cursor.fetchall()])


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
            # instead if we zoomed out too much, we limit to maximum 110km radius circle
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
