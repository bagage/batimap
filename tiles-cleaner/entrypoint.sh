#!/bin/sh

INIT_FILE="/data/initdb_is_done"
CACHE_DIR="/data/cache"
UPDATE_FILE=/data/outdated.txt
WORK_FILE=/data/inprogress.txt
INITIAL_MAX_ZOOM=${INITIAL_MAX_ZOOM:-10}

cd /app

echo "Starting tiles cleaner. Waiting for new events…"
while true; do
    if [ -f $INIT_FILE ]; then
        echo "Removing all tiles, will regenerate up to level $INITIAL_MAX_ZOOM!"
        # cache whole world at start, if needed
        rm -rf "$CACHE_DIR"/*
        echo "Regenerating up to level $INITIAL_MAX_ZOOM!"
        tegola --config /app/config.toml cache seed --max-zoom $INITIAL_MAX_ZOOM
        echo -n > $UPDATE_FILE
        rm $INIT_FILE
        echo "Initialization terminated"
    elif [ -s $UPDATE_FILE ]; then
        echo "There is $(wc -l $UPDATE_FILE) outdated tiles to treat..."
        cat $UPDATE_FILE | sort | uniq > $WORK_FILE
        echo -n > $UPDATE_FILE
        while read bbox; do
            # if bbox not empty
            if [ ! -z $bbox ]; then
                tegola --config /app/config.toml cache purge --bounds "$bbox" --min-zoom 7 --max-zoom 13
                tegola --config /app/config.toml cache seed --bounds "$bbox" --min-zoom 7 --max-zoom $INITIAL_MAX_ZOOM
            fi
        done < $WORK_FILE
        rm $WORK_FILE
        echo "All tiles treated!"
    fi
    sleep 30
 done
