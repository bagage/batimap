# How to contribute

## First steps before starting

### Database setup

```sh
# you can either install postgis or use a docker instance directly:
docker run --name "batimap_pg" -p 25432:5432 -d -t kartoza/postgis

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

# WARNING: the following command will remove ALL database. Add '--append --slime' parameters
# if you wish to keep your data!
osm2pgsql -H localhost -U docker -P 25432 --verbose --proj 4326 --hstore-all -W --database gis boundaries.pbf
```

### Backend setup

In `backend` directory, create a virtualenv then install python packages:

```sh
vf new -p python3 batimap
pip install -r requirements.txt
set -x FLASK_APP app.py
flask initdb
```

### Frontend setup

In `frontend` directory, install nodejs packages:

```sh
yarn
```

## Launch dev environment

1. Start postgis server or docker

```sh
docker start "batimap_pg"
```

1. Start backend

```sh
cd backend
vf activate batimap
set -x FLASK_APP app.py
flask start
```

1. Start frontend

```sh
cd frontend
yarn start
```
