#!/bin/bash

INIT_FILE="/data/initdb_is_done"
CACHE_DIR="/data/cache"
UPDATE_FILE=/data/outdated.txt
WORK_FILE=/data/inprogress.txt
INITIAL_MAX_ZOOM=${INITIAL_MAX_ZOOM:-10}
MIN_ZOOM=7
if [ $INITIAL_MAX_ZOOM -lt $MIN_ZOOM ]; then
    MIN_ZOOM=$((INITIAL_MAX_ZOOM - 1))
fi

cd /app

echo "Starting tiles cleaner. Waiting for new events…"
while true; do
    if [ -f $INIT_FILE ]; then
        # do not regenerate tiles outside France if they were already generated since they won't change
        if [ -d $CACHE_DIR/batimap/$INITIAL_MAX_ZOOM ]; then
            echo "Regenerating France only tiles up to level $INITIAL_MAX_ZOOM!"
            # bboxes from https://boundingbox.klokantech.com/
            france_bboxes=(
                "-5.45,41.26,9.87,51.27" # france metropolitan
                "-63.06639,17.670931,-62.584402,18.137557" # 970 st barthélémy
                "-61.809764,15.832008,-61.000366,16.514466" # 971 guadeloupe
                "-61.229082,14.388703,-60.809583,14.878703" # 972 Martinique
                "-54.6028,2.1122,-51.5694,5.978" # 973 Guyane
                "55.216427,-21.389731,55.836692,-20.871714" # 974 Réunion
                "-56.6973,46.5507,-55.9033,47.365" # 975 St Pierre et Miquelon
                "44.7437,-13.2733,45.507,-12.379" # 976 Mayotte
            )
            for bbox in "${france_bboxes[@]}"; do
                echo "Regenerating tiles in bbox $bbox"
                tegola --config /app/config.toml cache purge --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom 13
                tegola --config /app/config.toml cache seed --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom $INITIAL_MAX_ZOOM
            done
        else
            echo "Removing all tiles, will regenerate up to level $INITIAL_MAX_ZOOM!"
            rm -rf "$CACHE_DIR"/* # in case something failed previously
            echo "Generating up to level $INITIAL_MAX_ZOOM!"
            tegola --config /app/config.toml cache seed --max-zoom $INITIAL_MAX_ZOOM
        fi
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
                echo "Regenrating tiles in bbox $bbox"
                tegola --config /app/config.toml cache purge --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom 13
                tegola --config /app/config.toml cache seed --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom $INITIAL_MAX_ZOOM
            fi
        done < $WORK_FILE
        rm $WORK_FILE
        echo "All tiles treated!"
    fi
    sleep 30
 done
