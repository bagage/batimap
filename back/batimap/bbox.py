import re
from math import sqrt


class Bbox(object):
    def __init__(self, xmin, ymin, xmax, ymax):
        self.coords = [xmin, ymin, xmax, ymax]
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def __repr__(self):
        return f"{self.xmin},{self.ymin},{self.xmax},{self.ymax}"

    def max_distance(self):
        """
        Maximum distance from the center of the screen that this bbox may reach
        """
        return sqrt((self.xmax - self.xmin) ** 2 + (self.ymax - self.ymin) ** 2) / 2

    @staticmethod
    def from_pg(bbox_string):
        # cf https://docs.python.org/3/library/re.html#simulating-scanf
        # need to handle 10e3 notation too
        float_re = r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        box_re = re.compile(
            r"BOX\("
            + float_re
            + " "
            + float_re
            + ","
            + float_re
            + " "
            + float_re
            + r"\)"
        )

        groups = box_re.match(bbox_string).groups()

        return Bbox(
            float(groups[0]), float(groups[4]), float(groups[8]), float(groups[12])
        )
