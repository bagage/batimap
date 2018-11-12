#!/bin/bash

POSTGRES_PORT=${POSTGRES_PORT:-5432}

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
WORK_DIR=/app

cd $WORK_DIR

echo "downloading $regions"

for region in $regions; do
    echo "downloading $region.osm.pbf"
    file=$(basename $region).osm.pbf
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf || test -f $file
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf.md5 || test -f $file.md5
    md5sum -c $file.md5
done

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



connection_param="postgis://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
for region in $regions; do
    region=$(basename $region)
    echo "Preparing $region…"
    # only keep administrative boundaries and buildings
    imposm import -config config.json -connection $connection_param -read $region.osm.pbf -appendcache
done
imposm import -config config.json -connection $connection_param -write
imposm import -config config.json -connection $connection_param -deployproduction

echo "Imports done!"
