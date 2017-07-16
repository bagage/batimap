
def pseudo_distance(p1, p2):
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2


def ringArea(coords):
    """
        This is borrowed from mapbox/geojson-rewind

        Calculate the approximate area of the polygon were it projected onto
          the earth.  Note that this area will be positive if ring is oriented
          clockwise, otherwise it will be negative.

        Reference:
        Robert. G. Chamberlain and William H. Duquette, "Some Algorithms for
          Polygons on a Sphere", JPL Publication 07-03, Jet Propulsion
          Laboratory, Pasadena, CA, June 2007 http://trs-new.jpl.nasa.gov/dspace/handle/2014/40409

        Returns:
        {float} The approximate signed geodesic area of the polygon in square
          meters.
    """
    area = 0

    if len(coords) > 2:
        for i in range(len(coords)-1):
            p1 = coords[i]
            p2 = coords[i + 1]
            area += math.radians(p2[0] - p1[0]) * (2 + math.sin(
                math.radians(p1[1])) + math.sin(math.radians(p2[1])))

        radius = 6378137
        area = area * radius * radius / 2

    return area


def correctRings(rings):
    """
    Polygons should be rotating anticlockwise (right-hand rule)
    """
    if ringArea(rings[0]) > 0:
        rings[0].reverse()
    for i in range(len(rings)):
        if ringArea(rings[i]) < 0:
            rings[i].reverse()
    return rings


def lines_to_polygons(ways):
    """
    Note: there might be multiple polygons for a single set of ways
    """

    if not ways:
        return []

    polygons = []
    border = ways.pop(0)
    while ways:
        dist = -1
        closest = 0
        reverse = False
        for i in range(len(ways)):
            d = pseudo_distance(border[-1], ways[i][0])
            if i == 0 or d < dist:
                dist = d
                closest = i
                reverse = False
            d = pseudo_distance(border[-1], ways[i][-1])
            if d < dist:
                dist = d
                closest = i
                reverse = True
        n = ways.pop(closest)
        if reverse:
            n.reverse()

        if dist == 0:
            n.pop(0)
            border += n
        else:
            polygons.append(border)
            border = n

    polygons.append(border)

    polygons = correctRings(polygons)
    return polygons


def color_by_date(date):
    try:
        date = int(date)
    except:
        if date:
            if date != "unknown":
                log.warning('Unknown date "{}"! Using gray.'.format(date))
            return 'gray'
        else:
            log.warning('No buildings found! Using pink.')
            return 'pink'

    if date <= 2009:
        return '#f00'
    else:
        return COLORS[date]


def stats_to_txt(stats):
    out = ''
    dates = sorted(stats.items(), key=lambda t: t[1])
    dates.reverse()
    total = sum(stats.values())
    for date, val in dates:
        out += '{}\t{} ({:.1%})\n'.format(date, val, val / total)
    out += 'Total\t{}\n'.format(total)
    return out


def get_municipality_relations(department, insee=None, force_download=False):
    log.info('Fetch cities boundary for department {} (via {})'.format(
        department, API.endpoint))

    json_path = path.join(STATS_PATH, '{}-limits.json'.format(department))

    if not force_download and path.exists(json_path):
        with open(json_path) as fd:
            result = json.load(fd)
        if insee:
            result = [x for x in result if x.get(
                'tags').get('ref:INSEE') == insee]

        # sometimes, the geometry of some cities is not set (probably due to an overpass error)
        # in that case, we will requery overpass instead
        for x in result:
            found = False
            for y in x.get('members'):
                if y.get('type') == 'way' and not y.get('role'):
                    log.error(
                        "Missing role for {} - requerying Overpass".format(x.get('tags').get('name')))
                    result = None
                    found = True
                    break
            if found:
                break

        if result:
            log.debug('Use cache file {}'.format(json_path))
            return result

    request = """[out:json];
        relation
          [boundary="administrative"]
          [admin_level=8]
          ["ref:INSEE"~"^{}"];
        out geom qt;""".format(insee if insee else department)

    response = overpass_request_with_retries(request)

    relations = response.get('elements')
    relations.sort(key=lambda x: x.get('tags').get('ref:INSEE'))

    if not insee:
        log.debug('Write cache file {}'.format(json_path))
        with open(json_path, 'w') as fd:
            fd.write(json.dumps(relations))

    return relations


def get_geometry_for(relation):
    outer_ways = []
    for member in relation.get('members'):
        if member.get('role') == 'outer':
            way = []
            for point in member.get('geometry'):
                way.append((point.get('lon'), point.get('lat')))
            outer_ways.append(way)
    borders = lines_to_polygons(outer_ways)

    if not borders:
        log.warning('{} does not have borders'.format(
            relation.get('tags').get('name')))
        exit(1)
        return None
    else:
        return Polygon(borders)


def build_municipality_list(department, vectorized, given_insee=None, force_download=None, umap=False, database=None):
    """Build municipality list
    """
    department = department.zfill(2)

    txt_content = ''
    department_stats = []
    connection = None

    if database:
        (host, port, user, password, database) = database.split(":")
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, database=database)
        cursor = connection.cursor()

    counter = 0
    relations = get_municipality_relations(
        department, given_insee, force_download == "all")
    for relation in relations:
        counter += 1

        tags = relation.get('tags')
        insee = tags.get('ref:INSEE')
        name = tags.get('name')
        postcode = tags.get('addr:postcode')

        if insee in vectorized:
            vector = 'vector'
            try:
                relation_src = count_sources(
                    'relation', insee, force_download in ["all", "relations"])['sources']
                building_src = count_sources(
                    'building', insee, force_download in ["all", "buildings"])['sources']
            except overpass.errors.ServerRuntimeError as e:
                log.error(
                    "Fail to query overpass for {}. Consider reporting the bug: {}. Skipping".format(insee, e))
                continue

            dates = sorted(building_src.items(),
                           key=lambda t: t[1], reverse=True)
            date = dates[0][0] if len(dates) else None
            color = color_by_date(date)
            description = 'Building:\n{}\nRelation:\n{}'.format(
                stats_to_txt(building_src), stats_to_txt(relation_src))
        else:
            date = 'raster'
            vector = 'raster'
            color = 'black'
            description = 'Raster'

        municipality_border = Feature(
            properties={
                'insee': insee,
                'name': name,
                'postcode': postcode,
                'description': description,
            },
        )

        if umap:
            municipality_border.properties['_storage_options'] = {
                'color': color,
                'weight': '1',
                'fillOpacity': '0.5',
                'labelHover': True,
            }
        else:
            municipality_border.properties['color'] = color

        municipality_border.geometry = get_geometry_for(relation)

        if database:
            log.debug("Updating database")
            try:
                req = ("""
                    INSERT INTO color_city
                    VALUES ('{}', '{}', '{}', now())
                    ON CONFLICT (insee) DO UPDATE SET color = excluded.color, department = excluded.department
                    """.format(insee, color, department))
                # only update date if we did not use cache files for buildings
                if force_download in ["all", "buildings"]:
                    req += ", last_update = excluded.last_update"
                cursor.execute(req)
            except Exception as e:
                log.warning("Cannot write in database: " + str(e))
                pass

        log.info("{:.2f}% Treated {} - {} (last import: {})".format(100 *
                                                                    counter / len(relations), insee, name, date))

        department_stats.append(municipality_border)
        txt_content += '{},{},{},{}\n'.format(insee, name, postcode, vector)

    if connection:
        # commit database changes only after the whole loop to 1. speed up 2. avoid
        # semi-updated database in case of error in the middle
        connection.commit()

    # write geojson
    log.debug('Write {}.geojson'.format(department))
    geojson_path = path.join(STATS_PATH, '{}.geojson'.format(department))
    if path.exists(geojson_path) and given_insee:
        department_geojson = geojson.loads(open(geojson_path).read())
        found = False
        for municipality in department_geojson["features"]:
            if municipality["properties"]["insee"] == given_insee:
                found = True
                index = department_geojson["features"].index(municipality)
                department_geojson["features"] = department_geojson["features"][
                    :index] + department_stats + department_geojson["features"][index + 1:]
                break
        if not found:
            department_geojson["features"] += department_stats

    else:
        department_geojson = FeatureCollection(department_stats)

    with open(geojson_path, 'w') as fd:
        # we should not indent the GeoJSON because it drastically reduce the final size
        # (x10 or so)
        fd.write(geojson.dumps(department_geojson, indent=None, sort_keys=True))

    # write txt
    log.debug('Write {}-municipality.txt'.format(department))
    txt_path = path.join(STATS_PATH, '{}-municipality.txt'.format(department))
    with open(txt_path, 'w') as fd:
        fd.write(txt_content)


def get_bbox_for(insee):
    """
    Returns left/right/bottom/top (min and max latitude / longitude) of the
    bounding box around the INSEE code
    """
    relation = get_municipality_relations(department_for(insee), insee, False)
    city = pygeoj.new()
    city.add_feature(geometry=get_geometry_for(relation[0]))
    city.update_bbox()
    return city.bbox


def get_name_for(insee):
    log.info("Fetch name for {}".format(insee))

    csv_path = path.join(STATS_PATH, 'france-cities.csv')
    if not path.exists(csv_path):
        request = """
            area[boundary='administrative'][admin_level='2']['name'='France']->.a;
            relation[boundary="administrative"][admin_level=8](area.a)
        """

        response = overpass_request_with_retries(
            request, responseformat='csv("ref:INSEE","name")')
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in response.split("\n"):
                csv_writer.writerow(row.split("\t"))

    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        results = [x['name']
                   for x in csv_reader if x['ref:INSEE'] == insee]
        if len(results) == 0:
            log.critical("Cannot found city with INSEE {}.".format(insee))
            exit(1)
        elif len(results) == 1:
            return results[0]
        else:
            log.critical(
                "Too many cities with insee {} (total: {}). Please check insee.".format(insee, len(results)))
            exit(1)


def get_insee_for(name):
    log.info("Fetch INSEE for {}".format(name))

    csv_path = path.join(STATS_PATH, 'france-cities.csv')
    if not path.exists(csv_path):
        request = """
            area[boundary='administrative'][admin_level='2']['name'='France']->.a;
            relation[boundary="administrative"][admin_level=8](area.a)
        """

        response = overpass_request_with_retries(
            request, responseformat='csv("ref:INSEE","name")')
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for row in response.split("\n"):
                csv_writer.writerow(row.split("\t"))

    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        insee = [x['ref:INSEE']
                 for x in csv_reader if x['name'].startswith(name)]
        if len(insee) == 0:
            log.critical("Cannot found city with name {}.".format(name))
            exit(1)
        elif len(insee) == 1:
            return insee[0]
        elif len(insee) > 30:
            log.critical(
                "Too many cities with name {} (total: {}). Please check name.".format(name, len(insee)))
            exit(1)
        else:
            user_input = ""
            while user_input not in insee:
                user_input = input(
                    "More than one city found. Please enter your desired one from the following list:\n\t{}\n".format('\n\t'.join(insee)))
            return user_input


def get_vectorized_insee(department):
    department = department.zfill(2)
    log.info('Fetch list of vectorized cities in department {}'.format(department))
    json_path = path.join(STATS_PATH, '{}-cadastre.json'.format(department))

    if path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            return json.load(fd)

    vectorized = []
    response = requests.get(
        'http://cadastre.openstreetmap.fr/data/{0}/{0}-liste.txt'.format(department.zfill(3)))
    if response.status_code >= 400:
        log.critical('Unknown department {}'.format(department))
        exit(1)

    for _, code, _ in [line.split(maxsplit=2) for line in response.text.strip().split('\n')]:
        if department.startswith('97'):
            vectorized.append('{}{}'.format(department, code[3:]))
        else:
            vectorized.append('{}{}'.format(department, code[2:]))

    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(vectorized, indent=4))

    return vectorized


def count_sources(datatype, insee, force_download):
    log.debug('Count {} sources for {} (via {})'.format(
        datatype, insee, API.endpoint))

    json_path = path.join(DATA_PATH, '{}.{}.json'.format(insee, datatype))
    if not force_download and path.exists(json_path):
        log.debug('Use cache file {}'.format(json_path))
        with open(json_path) as fd:
            content = json.load(fd)
            if 'sources' in content and 'authors' in content:
                return content

    if datatype == 'building':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( node['building'](area.a);
              way['building'](area.a);
              relation['building'](area.a);
            );
            out tags qt meta;""".format(insee)
    elif datatype == 'relation':
        request = """[out:json];
            area[boundary='administrative'][admin_level='8']['ref:INSEE'='{}']->.a;
            ( way['building'](area.a);
              node(w)['addr:housenumber'];
            );
            out tags qt;""".format(insee)

    for retry in range(9, 0, -1):
        try:
            response = overpass_request_with_retries(request)
            break
        except (overpass.errors.MultipleRequestsError, overpass.errors.ServerLoadError) as e:
            log.warning("{} occurred. Will retry again {} times in a few seconds".format(
                type(e).__name__, retry))
            if retry == 0:
                raise e
            # Sleep for n * 5 seconds before a new attempt
            time.sleep(5 * round((10 - retry) / 3))

    sources = {}
    authors = {}
    for element in response.get('elements'):
        src = element.get('tags').get('source') or 'unknown'
        src = src.lower()
        src = re.sub(CADASTRE_PROG, r'\2', src)
        sources[src] = sources[src] + 1 if src in sources else 1

        author = element.get('user') or 'unknown'
        authors[author] = authors[author] + 1 if author in authors else 1
    content = {}
    content['sources'] = sources
    content['authors'] = authors
    log.debug('Write cache file {}'.format(json_path))
    with open(json_path, 'w') as fd:
        fd.write(json.dumps(content, sort_keys=True, indent=4))

    return content


def get_josm_path():
    for p in os.environ['PATH']:
        if p.lower().endswith("josm"):
            return p

    for d in [os.environ['HOME'] + "/.local/share/applications/", "/usr/share/applications", "/usr/local/share/applications"]:
        desktop = path.join(d, "josm.desktop")
        if os.path.exists(desktop):
            with open(desktop, 'r') as fd:
                for line in fd:
                    if "Exec=" in line:
                        # could probably be better
                        cmd = "=".join(line.split("=")[1:]).split(" ")
                        cmd = [x for x in cmd if not x.startswith("%")]
                        return cmd

    return None


def start_josm(base_url):
        # Hack: look in PATH and .desktop files if JOSM is referenced
    josm_path = get_josm_path()
    # If we found it, start it and try to connect to it (aborting after 1
    # min)
    if josm_path:
        stdouterr = None if log.getEffectiveLevel() == logging.DEBUG else subprocess.PIPE
        subprocess.Popen(josm_path, stdout=stdouterr, stderr=stdouterr)
        timeout = time.time() + 60
        while True:
            try:
                r = requests.get(base_url + 'version')
                if r.status_code == 200 or time.time() > timeout:
                    return True
            except:
                pass
        if time.time() > timeout:
            log.critical(
                "Cannot connect to JOSM - is it running? Tip: add JOSM to your PATH so that I can run it for you ;)")
    return False
