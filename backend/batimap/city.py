#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
import shutil
import tarfile
from contextlib import closing
from os import path
from bs4 import BeautifulSoup
import json
from collections import Counter
import requests
from pkg_resources import resource_stream

LOG = logging.getLogger(__name__)


class City(object):
    __insee_regex = re.compile("^[a-zA-Z0-9]{3}[0-9]{2}$")
    __cadastre_src2date_regex = re.compile(
        r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')
    __cadastre_code = resource_stream(
        __name__, 'code_cadastre.csv').read().decode().split('\n')
    __total_pdfs_regex = re.compile(
        ".*coupe la bbox en \d+ \* \d+ \[(\d+) pdfs\]$")

    BASE_PATH = "/tmp/batimap_data"  # fixme
    WORKDONE_PATH = path.join(BASE_PATH, '_done')
    WORKDONETAR_PATH = path.join(WORKDONE_PATH, 'tars')
    STATS_PATH = path.join(BASE_PATH, 'stats')
    DATA_PATH = path.join(STATS_PATH, 'cities')
    os.makedirs(WORKDONE_PATH, exist_ok=True)
    os.makedirs(WORKDONETAR_PATH, exist_ok=True)
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(STATS_PATH, exist_ok=True)

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
        idx = 3 if self.department.startswith('97') else 2

        for line in self.__cadastre_code:
            try:
                (d, _, cadastre_name, _, code_cadastre,
                 bati_type) = line.strip().split(',')
                if d == self.department and code_cadastre[idx:] == self.insee[idx:]:
                    self.name_cadastre = "{}-{}".format(
                        code_cadastre, cadastre_name)
                    self.is_vectorized = (bati_type == 'VECT')
                    break
            except Exception as e:
                pass

    def __repr__(self):
        return '{}({})'.format(self.name, self.insee)

    def get_last_import_date(self):
        return self.db.last_import_date(self.insee)

    def get_work_path(self):
        if self.name_cadastre is None:
            return None
        return path.join(City.BASE_PATH, "{}-{}".format(self.insee, self.name_cadastre))

    def get_bbox(self):
        return self.db.bbox_for_insee(self.insee)

    def fetch_cadastre_data(self, force=False):
        if self.name_cadastre is None:
            return False

        url = 'http://cadastre.openstreetmap.fr'

        dept = self.department.zfill(3)

        r = requests.get(f"{url}/data/{dept}/")
        bs = BeautifulSoup(r.content, "lxml")

        for e in bs.find_all('tr'):
            if f"{self.name_cadastre.upper()}.tar.bz2" in [x.text for x in e.select('td:nth-of-type(2) a')]:
                date = e.select('td:nth-of-type(3)')[0].text.strip()
                if (datetime.datetime.now() - datetime.datetime.strptime(date, "%d-%b-%Y %H:%M")).days > 30:
                    LOG.warn(f"{self.name_cadastre} was already generated at {date}, but is too old so refreshing it…")
                    force = True
                else:
                    LOG.info(f"{self.name_cadastre} was already generated at {date}, no need to regenerate it!")

        data = {
            'dep': dept,
            'type': 'bati',
            # fixme: if data is too old, we should ask for new generation
            'force': 'true' if force else 'false',
            'ville': self.name_cadastre,
        }

        # otherwise we invoke Cadastre generation
        with closing(requests.post(url, data=data, stream=True)) as r:
            total = 0
            current = 0
            for line in r.iter_lines(decode_unicode=True):
                # only display progression
                # TODO: improve this…
                if "coupe la bbox en" in line:
                    match = self.__total_pdfs_regex.match(line)
                    if match:
                        total = int(match.groups()[0])

                if line.endswith(".pdf"):
                    current += 1
                    msg = f"{current}/{total} ({current * 100.0 / total:.2f}%)" if total > 0 else f"{current}"
                    LOG.info(msg)
                elif "ERROR:" in line or "ERREUR:" in line:
                    LOG.error(line)
                    return False

        tarname = self.get_work_path() + '.tar.bz2'
        r = requests.get(
            "{}/data/{}/{}.tar.bz2".format(url, data['dep'], data['ville']))
        if r.status_code != 200:
            # try to regenerate cadastre data
            if not force:
                return self.fetch_cadastre_data(True)
            return False

        LOG.debug('Décompression du fichier {}'.format(tarname))
        with open(tarname, 'wb') as fd:
            fd.write(r.content)

        # finally decompress it and move to archive
        tar = tarfile.open(tarname)
        tar.extractall(path=self.get_work_path())
        tar.close()
        shutil.move(tarname, path.join(
            City.WORKDONETAR_PATH, path.basename(tarname)))
        return True

    def fetch_osm_data(self, overpass, force):
        date = self.get_last_import_date()
        if force or date is None:
            sources_date = []
            authors = []

            if not self.is_vectorized:
                date = 'raster'
            else:
                request = """[out:json];
                    area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
                    ( node['building'](area.a);
                      way['building'](area.a);
                      relation['building'](area.a);
                    );
                    out tags qt meta;""".format(self.insee)
                try:
                    response = overpass.request_with_retries(request)
                except Exception as e:
                    LOG.error(
                        "Failed to count buildings for {}: {}".format(self, e))
                    return (None, None)
                for element in response.get('elements'):
                    src = element.get('tags').get('source') or 'unknown'
                    src = re.sub(self.__cadastre_src2date_regex, r'\2', src.lower())
                    sources_date.append(src)

                    a = element.get('user') or 'unknown'
                    authors.append(a)

                date = max(sources_date, key=sources_date.count) if len(
                    sources_date) else 'never'
                date_match = self.__cadastre_src2date_regex.match(date)
                date = date_match.groups()[0] if date_match and date_match.groups() else 'unknown'

                LOG.debug(f"City stats: {Counter(sources_date)}")
            # only update date if we did not use cache files for buildings
            self.db.update_stats_for_insee(
                self.insee,
                date,
                json.dumps({'dates': Counter(sources_date),
                            'authors': Counter(authors)}),
                True
            )
        return date
