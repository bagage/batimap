#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import http.cookiejar
import logging
import re
import urllib.request
import zlib
from datetime import datetime
from collections import Counter
from contextlib import closing
from flask import current_app, g
import gzip
import requests
from bs4 import BeautifulSoup, SoupStrainer
from batimap.db import City, Cadastre
import json

LOG = logging.getLogger(__name__)


class ODCadastre(object):
    def init_app(self, db):
        self.db = db

    def query_city_od(self, insee):
        url = f"https://cadastre.data.gouv.fr/bundler/cadastre-etalab/communes/{insee}/geojson/batiments"
        r = requests.get(url)
        LOG.debug(f"parsing department od for {insee}")
        data = r.json()
        return len(data["features"])

    def query_department_od(self, dept):
        url = f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/departements/{dept}/cadastre-{dept}-batiments.json.gz"
        r = requests.get(url)
        LOG.debug(f"parsing department od for {dept}")
        data = json.loads(gzip.decompress(r.content))

        # there is one feature per building, properties.commune containing its city INSEE
        buildings_per_insee = Counter(
            [b["properties"]["commune"] for b in data["features"]]
        )

        return buildings_per_insee

    def compute_count(self, insee):
        if len(insee) == 2:
            # department
            result = self.department_count(insee)
        else:
            result = self.city_count(insee)

        self.db.session.commit()
        return result

    def department_count(self, insee):
        if not self.db.get_department(insee):
            return None

        counts = self.query_department_od(insee)
        result = [
            self.db.session.merge(Cadastre(insee, buildings))
            for (insee, buildings) in counts.items()
        ]

        self.db.session.add_all(result)

        return result

    def city_count(self, insee):
        if not self.db.get_city_for_insee(insee):
            return None

        try:
            buildings = self.query_city_od(insee)
        except Exception as e:
            current_app.logger.warning(f"could not fetch cadastre for {insee}: {e}")
            return None

        c = self.db.session.merge(Cadastre(insee, buildings))
        self.db.session.add(c)

        return c
