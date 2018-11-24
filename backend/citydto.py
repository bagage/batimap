from json import JSONEncoder


class CityDTO:
    name = None
    insee = None
    date = None
    josm_ready = False
    details = None

    def __init__(self, date, city=None, name=None, insee=None, details=None, josm_ready=None):
        self.date = date
        if city:
            self.name = city.name
            self.insee = city.insee
            self.details = city.details
            self.josm_ready = city.date_cadastre is not None
        else:
            self.name = name
            self.insee = insee
            self.details = details
            self.josm_ready = josm_ready

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
