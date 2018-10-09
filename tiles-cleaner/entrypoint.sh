#!/bin/sh

INPUT_FILE=/app/tiles-outdated.txt
WORK_FILE=/app/inprogress.txt

while true; do
    if [ ! -s $INPUT_FILE ]; then
        cp $INPUT_FILE $WORK_FILE
        tegola cache seed --overwrite --tile-list $WORK_FILE
        rm $WORK_FILE
        echo > $INPUT_FILE
    fi
done
