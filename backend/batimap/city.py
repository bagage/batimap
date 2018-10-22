#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import re
import json
from collections import Counter

LOG = logging.getLogger(__name__)


class City(object):
    __insee_regex = re.compile("^[a-zA-Z0-9]{3}[0-9]{2}$")
    __cadastre_src2date_regex = re.compile(
        r'.*(cadastre)?.*(20\d{2}).*(?(1)|cadastre).*')

    insee = None
    name = None
    department = None
    name_cadastre = None
    is_raster = False
    details = None
    date_cadastre = None

    __db = None

    def __init__(self, db, identifier):
        self.__db = db
        if self.__insee_regex.match(identifier) is not None:
            self.insee = identifier
            self.name = self.__db.name_for_insee(self.insee)
        else:
            self.name = identifier
            self.insee = self.__db.insee_for_name(self.name)

        if self.name and self.insee:
            data = db.city_data(self.insee, ["department", "name_cadastre", "is_raster", "details", "date_cadastre"])
            assert data and len(data) == 5
            (self.department, self.name_cadastre, self.is_raster, self.details, self.date_cadastre) = data
        else:
            self.name = None
            self.insee = None

    def __repr__(self):
        return f'{self.name}({self.insee})'

    def get_last_import_date(self):
        return self.__db.last_import_date(self.insee)

    def get_bbox(self):
        return self.__db.bbox_for_insee(self.insee)

    def fetch_osm_data(self, overpass, force):
        date = self.get_last_import_date()
        if force or date is None:
            sources_date = []
            if self.is_raster:
                date = 'raster'
            else:
                request = f"""[out:json];
                    area[boundary='administrative'][admin_level~'8|9']['ref:INSEE'='{self.insee}']->.a;
                    ( node['building'](area.a);
                      way['building'](area.a);
                      relation['building'](area.a);
                    );
                    out tags qt meta;"""
                try:
                    response = overpass.request_with_retries(request)
                except Exception as e:
                    LOG.error(f"Failed to count buildings for {self}: {e}")
                    return (None, None)
                for element in response.get('elements'):
                    src = element.get('tags').get('source') or 'unknown'
                    src = re.sub(self.__cadastre_src2date_regex, r'\2', src.lower())
                    sources_date.append(src)

                date = max(sources_date, key=sources_date.count) if len(
                    sources_date) else 'never'
                if date != 'never':
                    date_match = re.compile(r'^(\d{4})$').match(date)
                    date = date_match.groups()[0] if date_match and date_match.groups() else 'unknown'

                LOG.debug(f"City stats: {Counter(sources_date)}")
            # only update date if we did not use cache files for buildings
            self.details = {'dates': Counter(sources_date)}
            self.__db.update_stats_for_insee([(
                self.insee,
                self.name,
                date,
                json.dumps(self.details),
                True
            )])
        return date
