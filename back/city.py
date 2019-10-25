#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import re
import datetime
from dateutil import parser

LOG = logging.getLogger(__name__)


class City(object):
    __insee_regex = re.compile("^[a-zA-Z0-9]{3}[0-9]{2}$")

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
            data = db.city_data(
                self.insee, ["department", "name", "name_cadastre", "is_raster", "details", "date_cadastre"]
            )
            assert data and len(data) == 6
            (self.department, self.name, self.name_cadastre, self.is_raster, self.details, self.date_cadastre) = data
        else:
            self.name = None
            self.insee = None

    def __repr__(self):
        return f"{self.name}({self.insee})"

    def get_last_import_date(self):
        return self.__db.last_import_date(self.insee)

    def get_bbox(self):
        return self.__db.bbox_for_insee(self.insee)

    def is_josm_ready(self):
        return (
            self.date_cadastre is not None
            and (datetime.datetime.now() - parser.parse(str(self.date_cadastre))).days < 30
        )
