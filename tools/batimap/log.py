import logging
import sys

from colorlog import ColoredFormatter


class Log(object):
    log = None
    levels = {
        'no': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }

    def __init__(self, verbosity):
        log_level = self.levels[
            verbosity] if verbosity in self.levels else self.levels['info']
        logging.root.setLevel(log_level)
        if sys.stdout.isatty():
            formatter = ColoredFormatter(
                '%(asctime)s %(log_color)s%(message)s%(reset)s', "%H:%M:%S")
            stream = logging.StreamHandler()
            stream.setLevel(log_level)
            stream.setFormatter(formatter)
            self.log = logging.getLogger('pythonConfig')
            self.log.setLevel(log_level)
            self.log.addHandler(stream)
        else:
            logging.basicConfig(
                format='%(asctime)s %(message)s', datefmt="%H:%M:%S")
            self.log = logging
