import re


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def from_pg(from_string):
        # cf https://docs.python.org/3/library/re.html#simulating-scanf
        # need to handle 10e3 notation too
        float_re = r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        box_re = re.compile(r"POINT\(" + float_re + " " + float_re + r"\)")
        groups = box_re.match(from_string).groups()
        return Point(float(groups[4]), float(groups[0]))

    def __repr__(self):
        return f"{self.x},{self.y}"
