from json import JSONEncoder


class CityDTO():
    name = None
    insee = None
    date = None
    details = None

    def __init__(self, name, insee, date, details):
        self.name = name
        self.insee = insee
        self.date = date
        self.details = details

    def __init__(self, city, date):
        self.name = city.name
        self.insee = city.insee
        self.date = date
        self.details = city.details

    @property
    def __geo_interface__(self):
        return {
            'name': self.name,
            "insee": self.insee,
            "date": self.date,
            "details": self.details
        }


class CityEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
