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

if [ ! -f "/config/config.json" ]; then
    echo "Missing imposm config file, exitting!"
    exit 1
fi
if [ ! -f "/config/mapping.json" ]; then
    echo "Missing imposm mapping file, exitting!"
    exit 1
fi

DO_IMPORT=true
if [ "$FORCE_IMPORT" != "true" ]; then
    count=`PGPASSWORD=$POSTGRES_PASSWORD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "select count(*) from osm_buildings where osm_id > 0"`
    result=$?
    if [[ $result -eq 0 ]]; then
        if [[ $count -gt 0 ]]; then
            # do not reimport if there is already something in database to avoid erasing it
            echo "Database already ready, skipping!"
            DO_IMPORT=false
        fi
    fi
fi

connection_param="postgis://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"

if [ "$DO_IMPORT" = "true" ]; then
    SCRIPT_DIR=$(realpath $(dirname $0))
    WORK_DIR=/app

    cd $WORK_DIR

    echo "downloading $regions"

    for region in $regions; do
        echo "downloading $region.osm.pbf"
        file=$(basename $region).osm.pbf
        axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf || test -f $file
        axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf.md5 || test -f $file.md5
        echo "checking $region.osm.pbf file integrity"
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

    for region in $regions; do
        region=$(basename $region)
        echo "Preparing $region…"
        # only keep administrative boundaries and buildings
        imposm import -config /config/config.json -mapping /config/mapping.json -connection $connection_param -read $region.osm.pbf -appendcache -diff
    done
    echo "Writing to database…"
    imposm import -config /config/config.json -mapping /config/mapping.json -connection $connection_param -write
    echo "Deploying to database…"
    imposm import -config /config/config.json -mapping /config/mapping.json -connection $connection_param -deployproduction

    echo "Imports done!"
fi

imposm run -config /config/config.json -mapping /config/mapping.json -expiretiles-zoom 10 -connection $connection_param
