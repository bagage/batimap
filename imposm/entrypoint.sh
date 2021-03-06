#!/bin/bash

# allow the container to be started with `--user`
if [ "$1" = 'tegola' -a "$(id -u)" = '0' ]; then
	find . \! -user batimap -exec chown batimap '{}' +
	exec su batimap -- "$0" "$@"
fi

# wait for other containers to be ready
/wait-for-it.sh

POSTGRES_PORT=${POSTGRES_PORT:-5432}
if [ -z "$REGIONS" ]; then
    REGIONS=(
        france-latest
        france/guadeloupe-latest
        france/guyane-latest
        france/martinique-latest
        france/mayotte-latest
        france/reunion-latest
    )
    REGIONS=${REGIONS[@]}
fi

echo "Imposm running with regions: $REGIONS..."

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
    # wait for postgres to have started
    while ! PGPASSWORD=$POSTGRES_PASSWORD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "select 1" 1>/dev/null; do
        sleep 1
    done
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

    echo "will import $REGIONS regions in db, please wait..."

    for region in $REGIONS; do
        echo "downloading $region.osm.pbf"
        file=$(basename $region).osm.pbf
        if ! test -z "$REGIONS_URL"; then
            axel $REGIONS_URL/$region.osm.pbf
        else
            axel http://download.geofabrik.de/europe/$region.osm.pbf.md5
            (test -f $file && md5sum -c $file.md5 &>/dev/null) || (rm -f $file && axel http://download.geofabrik.de/europe/$region.osm.pbf)
            echo "checking $region.osm.pbf file integrity"
            md5sum -c $file.md5 || exit 1
        fi
    done

    echo "Waiting for postgis to be available..."
    while :
    do
        pg_isready -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB 1>/dev/null
        result=$?
        if [[ $result -eq 0 ]]; then
            break
        fi
        sleep 5
    done

    for region in $REGIONS; do
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

imposm run -config /config/config.json -mapping /config/mapping.json -connection $connection_param
