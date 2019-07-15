import re


class Point(object):

    # cf https://docs.python.org/3/library/re.html#simulating-scanf
    # need to handle 10e3 notation too
    float_re = r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
    box_re = re.compile(r"POINT\(" + float_re + " " + float_re + r"\)")

    def __init__(self, from_string):
        groups = self.box_re.match(from_string).groups()
        self.y = float(groups[0])
        self.x = float(groups[4])

    def __repr__(self):
        return f"{self.x},{self.y}"
