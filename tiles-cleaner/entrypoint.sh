#!/bin/bash

# allow the container to be started with `--user`
# if [ "$(id -u)" = '0' ]; then
# 	find /app \! -user batimap -exec chown batimap '{}' +
# 	exec su batimap -- "$0" "$@"
# fi

INIT_FILE="/data/flush_all_tiles"
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
            declare -A france_bboxes=(
                ["France metropolitan"]="-5.45,41.26,9.87,51.27"
                ["970 St Barthélémy"]="-63.06639,17.670931,-62.584402,18.137557"
                ["971 Guadeloupe"]="-61.809764,15.832008,-61.000366,16.514466"
                ["972 Martinique"]="-61.229082,14.388703,-60.809583,14.878703"
                ["973 Guyane"]="-54.6028,2.1122,-51.5694,5.978"
                ["974 Réunion"]="55.216427,-21.389731,55.836692,-20.871714"
                ["975 St Pierre et Miquelon"]="-56.6973,46.5507,-55.9033,47.365"
                ["976 Mayotte"]="44.7437,-13.2733,45.507,-12.379"
            )
            for zone in "${!france_bboxes[@]}"; do
                bbox="${france_bboxes[$zone]}"
                echo "Regenerating tiles for $zone in bbox $bbox"
                tegola --config /app/config.toml cache purge --bounds "$bbox" --max-zoom 11 1>/dev/null
                tegola --config /app/config.toml cache seed --bounds "$bbox" --max-zoom $INITIAL_MAX_ZOOM
            done
        else
            echo "Removing all tiles, will regenerate up to level $INITIAL_MAX_ZOOM!"
            rm -rf "$CACHE_DIR"/* # in case something failed previously
            echo "Generating up to level $INITIAL_MAX_ZOOM!"
            tegola --config /app/config.toml cache seed --max-zoom $INITIAL_MAX_ZOOM
        fi
        echo -n > $UPDATE_FILE
        rm -f -- $INIT_FILE
        echo "Tiles initial (re)generation terminated"
    elif [ -s $UPDATE_FILE ]; then
        echo "There is $(wc -l $UPDATE_FILE) outdated tiles to treat..."
        cat $UPDATE_FILE | sort | uniq > $WORK_FILE
        echo -n > $UPDATE_FILE
        while read bbox; do
            # if bbox not empty
            if [ ! -z $bbox ]; then
                echo "Regenerating tiles in bbox $bbox"
                tegola --config /app/config.toml cache purge --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom 11
                tegola --config /app/config.toml cache seed --bounds "$bbox" --min-zoom $MIN_ZOOM --max-zoom $INITIAL_MAX_ZOOM
            fi
        done < $WORK_FILE
        rm -f -- $WORK_FILE
        echo "All tiles treated!"
    fi
    sleep 30
 done
