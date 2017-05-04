#!/usr/bin/env python3

import sys
import os.path
import datetime
import csv
import json
from colour import Color

def color_for_date(date):
    colors = {
        "RASTER": "Black",
        None: "Gray",
    }

    # 2009 should be red,
    # current year should be green
    # previous year should be orange
    # below 2009 and previous year, use a color gradient
    this_year = datetime.datetime.now().year
    gradient_colors = list(Color("red").range_to(Color("orange"), this_year - 2009))
    for year in range(2009, this_year):
        colors[str(year)] = gradient_colors[year - 2009].hex
    colors[str(this_year)] = "Green"

    if date in colors:
        return colors[date]
    else:
        print("Unknown date! {}".format(date));
        return "#0000ff"

def csv2json(input_file, output_file):
    with open(input_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)

    features = []
    for row in rows:
        point = {}
        point["type"] = "Feature"
        point["properties"] = {}
        for key in ["1NSEE", "NOM", "COUNT", "DATE", "ASSOCIATEDSTREET"]:
            if row[key] is not None:
                point["properties"][key] = row[key].strip()
        date = row["DATE"].strip() if row["DATE"] is not None else None
        point["properties"]["_storage_options"] = {
            "color": color_for_date(date),
        }
        point["geometry"] = {
            "type": "Point",
            "coordinates": [
                row["LON"],
                row["LAT"]
            ]
        }

        features.append(point)


    collection = {}
    collection["type"] = "FeatureCollection"
    collection["features"] = features;

    with open(output_file, 'w') as f:
        json.dump(collection, f, indent=4)

if len(sys.argv) != 2:
    print("Please provide ONE argument: department to treat. Example: {} 26".format(sys.argv[0]))
else:
    this_path = os.path.dirname(os.path.realpath(__file__))
    input_file = "{}/../data/stats/{}-statistics.csv".format(this_path, sys.argv[1])
    output_file = input_file.replace(".csv", ".geojson")
    if not os.path.isfile(input_file):
        print("{} does not exist.".format(input_file))
    else:
        csv2json(input_file, output_file)
