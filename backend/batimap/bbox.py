import re


class Bbox(object):

    str_regex = re.compile(
        r'BOX\((-{0,1}[\d\.]+) (-{0,1}[\d\.]+),(-{0,1}[\d\.]+) (-{0,1}[\d\.]+)\)')

    def __init__(self, from_string):
        groups = self.str_regex.match(from_string).groups()
        self.xmin = float(groups[0])
        self.ymin = float(groups[1])
        self.xmax = float(groups[2])
        self.ymax = float(groups[3])

    def __repr__(self):
        return f'{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}'
