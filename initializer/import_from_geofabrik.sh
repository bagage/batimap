#!/bin/bash

if [ $# -gt 0 ]; then
    regions="$@"
else
    regions=(
        france-latest
        france/guadeloupe-latest
        france/guyane-latest
        france/martinique-latest
        france/mayotte-latest
        france/reunion-latest
    )
    regions=${regions[@]}
fi

echo "Preparing postgre database with regions: $regions..."

if [ -z $POSTGRES_PASSWORD ] || [ -z $POSTGRES_USER ] || [ -z $POSTGRES_HOST ] || [ -z $POSTGRES_PORT ] || [ -z $POSTGRES_DB ]; then
    echo "Missing postgres environment variable for script, exitting!"
    exit 1
fi

count=`PGPASSWORD=$POSTGRES_PASSWORD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "select count(*) from buildings_osm_polygon where osm_id > 0" 2>/dev/null`
result=$?
if [[ $result -eq 0 ]]; then
    if [[ $count -gt 0 ]]; then
        # do not reimport if there is already something in database to avoid erasing it
        echo "Database already ready, skipping!"
        exit 0
    fi
fi

set -e

SCRIPT_DIR=$(realpath $(dirname $0))
WORK_DIR=/tmp/batimap-init

mkdir -p $WORK_DIR
cd $WORK_DIR

for region in $regions; do
    file=$(basename $region).osm.pbf
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf || test -f $file
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf.md5 || test -f $file.md5
    md5sum -c $file.md5
done

for region in $regions; do
    region=$(basename $region)
    echo "Preparing $region…"
    # only keep administrative boundaries and buildings
    test -f ${region}_boundaries.osm.pbf || osmium tags-filter $region.osm.pbf "type=boundary,boundary=administrative" -o ${region}_boundaries.osm.pbf
    test -f ${region}_buildings.osm.pbf || osmium tags-filter $region.osm.pbf "building" -o ${region}_buildings.osm.pbf
done

echo "Persisting in db…"
osmium merge --overwrite *_boundaries.osm.pbf -o boundaries.osm.pbf
osmium merge --overwrite *_buildings.osm.pbf -o buildings.osm.pbf

echo "Waiting for postgis to be available..."
while :
do
    pg_isready -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB
    result=$?
    if [[ $result -eq 0 ]]; then
        echo "$cmdname: postgis is available"
        break
    fi
    sleep 5
done

PGPASSWORD=$POSTGRES_PASSWORD osm2pgsql -C 6000Mo -H $POSTGRES_HOST -U $POSTGRES_USER -P $POSTGRES_PORT \
    --verbose --proj 4326 --database $POSTGRES_DB boundaries.osm.pbf \
    --style $SCRIPT_DIR/osm2pgsql.style --slim --flat-nodes osm2pgsql.flatnodes
PGPASSWORD=$POSTGRES_PASSWORD osm2pgsql -C 6000Mo -H $POSTGRES_HOST -U $POSTGRES_USER -P $POSTGRES_PORT \
    --verbose --proj 4326 --database $POSTGRES_DB --prefix buildings_osm buildings.osm.pbf \
    --style $SCRIPT_DIR/osm2pgsql.style --slim --flat-nodes osm2pgsql.flatnodes

rm osm2pgsql.flatnodes

echo "Imports done!"
