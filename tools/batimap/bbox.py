import re


class Bbox(object):

    str_regex = re.compile(
        'BOX\((-{0,1}[\d\.]+) (-{0,1}[\d\.]+),(-{0,1}[\d\.]+) (-{0,1}[\d\.]+)\)')

    def __init__(self, from_string):
        (self.xmin, self.ymin, self.xmax,
         self.ymax) = self.str_regex.match(from_string).groups()
