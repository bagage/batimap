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

    def __init__(self, db, identifier):
        self.db = db
        if self.__insee_regex.match(identifier) is not None:
            self.insee = identifier
            self.name = self.db.name_for_insee(self.insee)
        else:
            self.name = identifier
            self.insee = self.db.insee_for_name(self.name)

        data = db.city_data(self.insee, ["department", "name_cadastre", "is_raster"])
        assert len(data) == 3
        self.department, self.name_cadastre, self.is_raster = data

    def __repr__(self):
        return f'{self.name}({self.insee})'

    def get_last_import_date(self):
        return self.db.last_import_date(self.insee)

    def get_bbox(self):
        return self.db.bbox_for_insee(self.insee)

    def fetch_osm_data(self, overpass, force):
        date = self.get_last_import_date()
        if force or date is None:
            sources_date = []
            authors = []

            if not self.is_raster:
                date = 'raster'
            else:
                request = f"""[out:json];
                    area[boundary='administrative'][admin_level='8']['ref:INSEE'='{self.insee}']->.a;
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
