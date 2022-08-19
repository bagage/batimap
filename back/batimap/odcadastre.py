#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
from collections import Counter
from datetime import datetime

import ijson
import requests
from batimap.db import Cadastre
from flask import current_app


class ODCadastre(object):
    def init_app(self, db):
        self.db = db

    def query_od(self, dept, city=None) -> Counter:
        url = "https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/"
        if city:
            url += f"communes/{dept}/{city}/cadastre-{city}-batiments.json.gz"
        else:
            url += f"departements/{dept}/cadastre-{dept}-batiments.json.gz"

        cadastre = self.db.get_cadastre_for_insee(city or dept)
        if cadastre:
            last_modified = requests.head(url).headers["Last-Modified"]
            if last_modified:
                last_modified_date = datetime.strptime(
                    last_modified, "%a, %d %b %Y %H:%M:%S %Z"
                )
                if last_modified_date < cadastre.last_fetch:
                    current_app.logger.debug(
                        f"cadastre fetched version {cadastre.last_fetch} is newer that latest available "
                        f"version {last_modified_date} for {city or dept}, using cache instead {cadastre}"
                    )
                    return Counter([city] * cadastre.od_buildings) if city else None

        r = requests.get(url)

        if r.status_code != 200:
            current_app.logger.warn(
                f"cadastre fetch failed (url={url}, status={r.status_code})"
            )
            return None

        data = gzip.decompress(r.content)

        # there is one feature per building, properties.commune containing its city INSEE
        buildings_per_insee = Counter(
            list(ijson.items(data, "features.item.properties.commune"))
        )

        return buildings_per_insee

    def query_department_od(self, dept) -> Counter:
        return self.query_od(dept)

    def query_city_od(self, insee) -> Counter:
        dept = insee[:3] if insee.startswith("97") else insee[:2]
        return self.query_od(dept, insee)

    def compute_count(self, insee) -> Cadastre:
        if len(insee) <= 3:
            result = self.department_count(insee)
        else:
            result = self.city_count(insee)

        self.db.session.commit()
        return result

    def department_count(self, dept) -> Cadastre:
        if not self.db.get_department(dept):
            return None

        cadastre_dept = self.db.get_cadastre_for_insee(dept)
        counts = self.query_department_od(dept)

        if counts:
            items = [
                self.db.session.merge(Cadastre(insee, dept, buildings))
                for (insee, buildings) in counts.items()
            ]
            # save a department Cadastre model too just to keep the date
            cadastre_dept = self.db.session.merge(
                Cadastre(dept, dept, sum(counts.values()))
            )
            items.append(cadastre_dept)

            self.db.session.add_all(items)

        return cadastre_dept

    def city_count(self, insee) -> Cadastre:
        if not self.db.get_city_for_insee(insee):
            return None

        cadastre = self.db.get_cadastre_for_insee(insee)
        try:
            counts = self.query_city_od(insee)
            if counts:
                cadastre = self.db.session.merge(
                    Cadastre(insee, insee[:-3], sum(counts.values()))
                )
                self.db.session.add(cadastre)
        except Exception as e:
            current_app.logger.warning(f"could not fetch cadastre for {insee}: {e}")

        return cadastre
