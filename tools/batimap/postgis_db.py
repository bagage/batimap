import psycopg2

from bbox import Bbox


class PostgisDb(object):

    def __init__(self, log, host, port, user, passw, db):
        self.log = log
        self.connection = psycopg2.connect(
            database=db, user=user, password=passw, port=port, host=host)
        self.cursor = self.connection.cursor()

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
            self.log.critical("Cannot found city with name {}.".format(name))
            exit(1)
        elif len(results) == 1:
            return results[0][0]
        elif len(results) > 30:
            self.log.critical(
                "Too many cities name starting with {} (total: {}). Please check name.".format(name, len(results)))
            exit(1)
        elif interactive:
            user_input = ''
            while user_input not in [x[0] for x in results]:
                user_input = input(
                    "More than one city found. Please enter your desired one from the following list:\n\t{}\n".format('\n\t'.join(['{} - {}'.format(x[0], x[1]) for x in results])))
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
            self.cursor.execute(req, [insee, color, department, author])
            self.connection.commit()
        except Exception as e:
            self.log.warning("Cannot write in database: " + str(e))
            pass
