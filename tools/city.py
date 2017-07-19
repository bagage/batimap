import re
import requests
from os import path
import shutil
import tarfile
from colour import Color
import datetime
from contextlib import closing
from statistics import mode
import os

BASE_PATH = path.normpath(
    path.join(path.dirname(path.realpath(__file__)), '..', 'data'))
WORKDONE_PATH = path.join(BASE_PATH, '_done')
WORKDONETAR_PATH = path.join(WORKDONE_PATH, 'tars')
STATS_PATH = path.join(BASE_PATH, 'stats')
DATA_PATH = path.join(STATS_PATH, 'cities')
os.makedirs(WORKDONE_PATH, exist_ok=True)
os.makedirs(WORKDONETAR_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(STATS_PATH, exist_ok=True)


class City(object):
    __insee_regex = re.compile("[a-zA-Z0-9]{3}[0-9]{2}")
    __cadastre_src2date_regex = re.compile(
        r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')

    def __init__(self, db, identifier):
        self.db = db
        if self.__insee_regex.match(identifier) is not None:
            self.insee = identifier
            self.name = db.name_for_insee(identifier)
        else:
            self.name = identifier
            self.insee = db.insee_for_name(identifier)

        # Format of INSEE is [0-9]{2}[0-9]{3} OR 97[0-9]{1}[0-9]{2} for overseas
        # the first part is the department number, the second the city
        # unique id
        if self.insee.startswith('97'):
            self.department = self.insee[:-2]
        else:
            self.department = self.insee[:-3]

        # get cadastre name and code
        self.name_cadastre = None
        self.is_vectorized = False
        response = requests.get(
            'http://cadastre.openstreetmap.fr/data/{0}/{0}-liste.txt'.format(self.department.zfill(3)))
        idx = 3 if self.department.startswith('97') else 2
        for _, code, cname in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
            if code[idx:] == self.insee[idx:]:
                self.name_cadastre = "{}-{}".format(code, cname.split('"')[1])
                self.is_vectorized = True
                break

    def __repr__(self):
        return '{} - {}'.format(self.insee, self.name)

    def date_color_dict(self):
        # Retrieve the last cadastre import for the given insee municipality.
        # 2009 and below should be red,
        # current year should be green
        # previous year should be orange
        # below 2009 and previous year, use a color gradient
        this_year = datetime.datetime.now().year
        colors = list(Color('red').range_to(Color('orange'), this_year - 2009))
        colors.append(Color('green'))
        d = dict(zip(range(2009, this_year + 1), [c.hex for c in colors]))
        d['raster'] = 'black'
        d['unknown'] = 'gray'
        d['never'] = 'pink'
        return d

    def get_last_import_date(self):
        color = self.db.last_import_color(self.insee)
        date2color = self.date_color_dict()
        date = [d for (d, c) in date2color.items() if c == color]
        return date[0] if len(date) else 'unknown'

    def get_last_import_author(self):
        return self.db.last_import_author(self.insee)

    def get_work_path(self):
        if self.name_cadastre is None:
            return None
        return path.join(BASE_PATH, "{}-{}".format(self.insee, self.name_cadastre))

    def get_bbox(self):
        return self.db.bbox_for_insee(self.insee)

    def fetch_cadastre_data(self):
        if self.name_cadastre is None:
            return False

        url = 'http://cadastre.openstreetmap.fr'
        data = {
            'dep': self.department.zfill(3),
            'type': 'bati',
            'force': False,
            'ville': self.name_cadastre,
        }

        # otherwise we invoke Cadastre generation
        with closing(requests.post(url, data=data, stream=True)) as r:
            for line in r.iter_lines(decode_unicode=True):
                # only display progression
                # TODO: improve this…
                if "pdf" in line:
                    log.info(line)

        tarname = self.get_work_path() + '.tar.bz2'
        r = requests.get(
            "http://cadastre.openstreetmap.fr/data/{}/{}.tar.bz2".format(data['dep'], data['ville']))
        log.debug('Décompression du fichier {}'.format(tarname))
        with open(tarname, 'wb') as fd:
            fd.write(r.content)

        # finally decompress it and move to archive
        tar = tarfile.open(tarname)
        tar.extractall(path=self.get_work_path())
        tar.close()
        shutil.move(tarname, path.join(
            WORKDONETAR_PATH, path.basename(tarname)))
        return True

    def fetch_osm_data(self, overpass, force):
        date = self.get_last_import_date()
        author = self.get_last_import_author()
        if force or date is None or author is None:
            if not self.is_vectorized:
                date = 'raster'
            elif force:
                request = """[out:json];
                    area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
                    ( node['building'](area.a);
                      way['building'](area.a);
                      relation['building'](area.a);
                    );
                    out tags qt meta;""".format(self.insee)
                response = overpass.request_with_retries(request)
                sources_date = []
                authors = []
                for element in response.get('elements'):
                    src = element.get('tags').get('source') or 'unknown'
                    src = re.sub(self.__cadastre_src2date_regex,
                                 r'\2', src.lower())
                    sources_date.append(src)

                    a = element.get('user') or 'unknown'
                    authors.append(a)

                author = mode(authors) if len(authors) else None
                date = mode(sources_date) if len(sources_date) else 'never'

        # only update date if we did not use cache files for buildings
        self.db.update_stats_for_insee(
            self.insee, self.date_color_dict().get(date, 'gray'), self.department, author, update_time=force)

        return (date, author)
