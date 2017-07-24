Inspired by [Matus Cimerman](https://github.com/cimox/python-leaflet-gis).

## Setup

## Database setup

```sh
# you can either install postgis or use a docker instance directly:
docker run --name "postgis" -p 25432:5432 -d -t kartoza/postgis

# download data from http://download.geofabrik.de/europe/, for instance:
wget http://download.geofabrik.de/europe/france/corse-latest.osm.pbf -O my-region.osm.pbf
# or for whole france (incl. overseas departments):
# osmium is in osmium-tool on Debian
wget http://download.geofabrik.de/europe/france-latest.osm.pbf http://download.geofabrik.de/europe/france/{guadeloupe,guyane,martinique,mayotte,reunion}-latest.osm.pbf
osmium merge *.pbf -o my-region.osm.pbf


# then filter data (osmconvert and osmfilter binaries are located in osmctools on Debian)
osmconvert -v my-region.osm.pbf -o=./my-region.o5m && \
osmfilter --keep="type=boundary and boundary=administrative" -v my-region.o5m -o=boundaries.o5m && \
osmconvert -v --out-pbf boundaries.o5m > boundaries.pbf

# WARNING: the following command will remove ALL database. Add '--append --slime' parameters if you wish
# to keep your data!
osm2pgsql -H localhost -U docker -P 25432 --verbose --proj 4326 --hstore-all -W --database gis boundaries.pbf

# finally create the only custom table we need
psql -h localhost -U docker -p 25432 -d gis -c "
CREATE TABLE IF NOT EXISTS color_city(insee TEXT PRIMARY KEY NOT NULL, department CHAR(3) NOT NULL, color CHAR(20), last_update TIMESTAMP, last_author TEXT);
CREATE INDEX insee_idx ON planet_osm_polygon ((tags->'ref:INSEE'))
"

# fill color information by running something like (may take few hours)
batimap.py --database 'localhost:25432:docker:docker:gis' stats -d `seq 1 1 19` 2A 2B `seq 21 1 95` `seq 971 1 976`
```

## Start

```sh
pip3 install -r requirements.txt
# modify app.conf with your database settings
FLASK_DEBUG=1 FLASK_APP=app.py flask run
open http://localhost:5000
```

## Tile server

Instead of using `http://cadastre.damsy.net/tegola/maps/bati/{z}/{x}/{y}.vector.pbf`
as vector tile server, you can run your own instance of [Tegola](https://http://tegola.io/).
`tegola-config.toml` is the configuration file used for this project.
