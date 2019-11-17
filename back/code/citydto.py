from json import JSONEncoder

import datetime
from dateutil import parser


class CityDTO:
    name = None
    insee = None
    date = None
    josm_ready = False
    details = None

    def __init__(self, date, city=None, name=None, insee=None, details=None, date_cadastre=None):
        self.date = date
        if city:
            self.name = city.name
            self.insee = city.insee
            self.details = city.details
            self.josm_ready = city.is_josm_ready()
        else:
            self.name = name
            self.insee = insee
            self.details = details
            # this check should be useless...
            if isinstance(date_cadastre, str):
                date_cadastre = parser.parse(date_cadastre)
            self.josm_ready = (
                date_cadastre is not None and (datetime.datetime.now() - date_cadastre).days < 30
            )

    @property
    def __geo_interface__(self):
        return {
            "name": self.name,
            "insee": self.insee,
            "date": self.date,
            "details": self.details,
            "josm_ready": self.josm_ready,
        }


class CityEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
