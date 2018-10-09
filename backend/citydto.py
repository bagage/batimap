from json import JSONEncoder


class CityDTO():
    name = None
    insee = None
    date = None
    josm_ready = False
    details = None

    def __init__(self, name, insee, date, details, josm_ready):
        self.name = name
        self.insee = insee
        self.date = date
        self.details = details
        self.josm_ready = josm_ready

    def __init__(self, city, date):
        self.name = city.name
        self.insee = city.insee
        self.date = date
        self.details = city.details
        self.josm_ready = city.date_cadastre is not None

    @property
    def __geo_interface__(self):
        return {
            'name': self.name,
            "insee": self.insee,
            "date": self.date,
            "details": self.details,
            "josm_ready": self.josm_ready,
        }


class CityEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
