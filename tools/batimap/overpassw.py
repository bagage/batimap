import time

import overpass as o


class Overpassw(object):
    __api = None

    endpoints = {
        'overpass.de': 'https://overpass-api.de/api/interpreter',
        'api.openstreetmap.fr': 'http://api.openstreetmap.fr/oapi/interpreter',
        'dev.api.openstreetmap.fr': 'http://dev.api.openstreetmap.fr/overpass',
        # default port/url for docker image
        'localhost': 'http://localhost:5001/api/interpreter'
    }

    def __init__(self, log, e):
        default = 'overpass.de'
        default = self.endpoints[
            e] if e in self.endpoints else self.endpoints[default]
        self.__api = o.API(endpoint=default, timeout=300)
        self.log = log

    def request_with_retries(self, request, output_format='json'):
        for retry in range(9, 0, -1):
            try:
                return self.__api.Get(
                    request, responseformat=output_format, build=False)
            except (o.errors.MultipleRequestsError, o.errors.ServerLoadError) as e:
                self.log.warning("{} occurred. Will retry again {} times in a few seconds".format(
                    type(e).__name__, retry))
                if retry == 0:
                    raise e
                # Sleep for n * 5 seconds before a new attempt
                time.sleep(5 * round((10 - retry) / 3))
        return None
