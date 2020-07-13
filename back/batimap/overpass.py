import logging
import time

import overpass

LOG = logging.getLogger(__name__)


class Overpass(object):
    # from https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances
    instances_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "http://overpass.openstreetmap.fr/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    def __init__(self):
        self.__apis = []
        self.__request = 0
        for uri in self.instances_endpoints:
            self.__apis.append(overpass.API(endpoint=uri, timeout=300))

    def request_with_retries(self, request, output_format="json"):
        apis = len(self.__apis)
        for retry in range(9, 0, -1):
            try:
                self.__request += 1
                api = self.__apis[self.__request % apis]
                LOG.warning(f"Executing Overpass on server {api.endpoint} with request:\n{request}")
                return api.Get(request, responseformat=output_format, build=False)
            except (overpass.errors.MultipleRequestsError, overpass.errors.ServerLoadError) as e:
                LOG.warning("{} occurred. Will retry again {} times in a few seconds".format(type(e).__name__, retry))
                if retry == 0:
                    raise e
                # Sleep for n * 5 seconds before a new attempt
                time.sleep(5 * round((10 - retry) / 3))
        return None

    def get_city_buildings(self, city):
        """
        Compute the latest import date for given city
        """
        request = f"""[out:json];
            area[boundary='administrative'][admin_level~'8|9']['ref:INSEE'='{city.insee}']->.a;
            (
              node['building'](area.a);
              way['building'](area.a);
              relation['building'](area.a);
            );
            out tags qt meta;"""
        return self.request_with_retries(request).get("elements")
