import logging
import time

import overpass as o

LOG = logging.getLogger(__name__)


class Overpass(object):

    def __init__(self, uri='https://overpass-api.de/api/interpreter'):
        self.__api = o.API(endpoint=uri, timeout=300)

    def request_with_retries(self, request, output_format='json'):
        for retry in range(9, 0, -1):
            try:
                LOG.debug(f"Executing Overpass request:\n{request}")
                return self.__api.Get(
                    request, responseformat=output_format, build=False)
            except (o.errors.MultipleRequestsError, o.errors.ServerLoadError) as e:
                LOG.warning("{} occurred. Will retry again {} times in a few seconds".format(
                    type(e).__name__, retry))
                if retry == 0:
                    raise e
                # Sleep for n * 5 seconds before a new attempt
                time.sleep(5 * round((10 - retry) / 3))
        return None
