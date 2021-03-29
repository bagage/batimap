from json import JSONEncoder

from .db import City


class CityDTO:
    name = None
    insee = None
    date = None
    josm_ready = False
    details = None

    def __init__(self, city: City):
        self.date = city.import_date
        self.name = city.name
        self.insee = city.insee
        self.details = city.import_details
        self.buildings = city.buildings
        self.josm_ready = city.is_josm_ready()

    @property
    def __geo_interface__(self):
        return {
            "name": self.name,
            "insee": self.insee,
            "date": self.date,
            "details": self.details,
            "buildings": self.buildings,
            "josm_ready": self.josm_ready,
        }


class CityEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
