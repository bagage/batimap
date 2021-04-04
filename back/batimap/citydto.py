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
        self.osm_buildings = city.osm_buildings
        self.od_buildings = city.cadastre.od_buildings if city.cadastre else None
        self.josm_ready = city.is_josm_ready()

    @property
    def __geo_interface__(self):
        return self.__dict__


class CityEncoder(JSONEncoder):
    def default(self, city):
        return city.__dict__
