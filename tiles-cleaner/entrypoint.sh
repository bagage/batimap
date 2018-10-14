#!/bin/sh

INPUT_FILE=/app/data/outdated/outdated.txt
WORK_FILE=/app/data/outdated/inprogress.txt

cd /app
while true; do
    if [ -s $INPUT_FILE ]; then
        echo "There is $(wc -l $INPUT_FILE) outdated tiles to treat..."
        cat $INPUT_FILE | sort | uniq > $WORK_FILE
        tegola cache purge --tile-list $WORK_FILE --max-zoom 8
        tegola cache seed --tile-list $WORK_FILE --max-zoom 8
        rm $WORK_FILE
        echo -n > $INPUT_FILE
        echo "All tiles treated!"
    fi
    sleep 30
done
