import re


class Bbox(object):

    # cf https://docs.python.org/3/library/re.html#simulating-scanf
    # need to handle 10e3 notation too
    float_re = r'([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)'
    box_re = re.compile(r'BOX\(' + float_re + ' ' + float_re + ',' + float_re + ' ' + float_re + r'\)')

    def __init__(self, from_string):
        groups = self.box_re.match(from_string).groups()
        self.xmin = float(groups[0])
        self.ymin = float(groups[4])
        self.xmax = float(groups[8])
        self.ymax = float(groups[12])

    def __repr__(self):
        return f'{self.xmin},{self.ymin},{self.xmax},{self.ymax}'
