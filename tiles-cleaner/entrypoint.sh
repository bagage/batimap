#!/bin/sh

INIT_FILE="/app/data/outdated/initdb_is_done"
UPDATE_FILE=/app/data/outdated/outdated.txt
WORK_FILE=/app/data/outdated/inprogress.txt
INITIAL_MAX_ZOOM=${INITIAL_MAX_ZOOM:-10}

cd /app

while true; do
    if [ -f $INIT_FILE ]; then
        echo "Resetting all tiles!"
        # cache whole world at start, if needed
        rm -rf data/cache/*
        tegola --config /app/config.toml cache seed --max-zoom $INITIAL_MAX_ZOOM
        echo -n > $UPDATE_FILE
        rm $INIT_FILE
    elif [ -s $UPDATE_FILE ]; then
        echo "There is $(wc -l $UPDATE_FILE) outdated tiles to treat..."
        cat $UPDATE_FILE | sort | uniq > $WORK_FILE
        echo -n > $UPDATE_FILE
        while read bbox; do
            # if bbox not empty
            if [ ! -z $bbox ]; then
                tegola --config /app/config.toml cache purge --bounds "$bbox" --min-zoom 8 --max-zoom 13
                tegola --config /app/config.toml cache seed --bounds "$bbox" --min-zoom 8 --max-zoom 10
            fi
        done < $WORK_FILE
        rm $WORK_FILE
        echo "All tiles treated!"
    fi
    sleep 30
 done
