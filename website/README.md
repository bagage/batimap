Inspired by [Matus Cimerman](https://github.com/cimox/python-leaflet-gis).

## Setup

## Database setup

```sh
# you can either install postgis or use a docker instance directly:
docker run --name "postgis" -p 25432:5432 -d -t kartoza/postgis

# then fill data in from http://download.geofabrik.de/europe/
# (these binaries are located in osmctools on Debian)
osmconvert france-latest.osm.pbf -v -o=./france-latest.o5m && \
osmfilter france-latest.o5m --keep="type=boundary and boundary=administrative" -v -o=boundaries.o5m && \
osmconvert boundaries.o5m -v --out-pbf > boundaries.pbf

osm2pgsql -H localhost -U docker -P 25432 --create --verbose --proj 4326 --hstore-all -W --database gis boundaries.pbf

# finally create the only custom table we need
/usr/lib/postgresql/9.6/bin/psql -h localhost -U docker -p 25432 -d gis -c 'create table if not exists color_city(insee TEXT PRIMARY KEY NOT NULL, color CHAR(20))'

# fill color information by running something like (may take few hours)
for i in `seq 1 1 19` 2A 2B `seq 21 1 95` `seq 971 1 976`; do
    echo $i ; osm-cadastre.py --verbose=warning stats -d $i
done
```

## Start

```sh
pip3 install -r requirements.txt
# modify app.conf with your database settings
FLASK_DEBUG=1 FLASK_APP=app.py flask run
open http://localhost:5000
```
