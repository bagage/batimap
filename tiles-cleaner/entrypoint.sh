#!/bin/sh -x

INPUT_FILE=/app/data/outdated/outdated.txt
WORK_FILE=/app/data/outdated/inprogress.txt

cd /app

# cache whole world at start, if needed
rm -rf data/cache/*
tegola cache seed --max-zoom 10

while true; do
    if [ -s $INPUT_FILE ]; then
        echo "There is $(wc -l $INPUT_FILE) outdated tiles to treat..."
        cat $INPUT_FILE | sort | uniq > $WORK_FILE
        while read bbox; do
            tegola cache purge --bounds "$bbox" --min-zoom 8 --max-zoom 13
            tegola cache seed --bounds "$bbox" --min-zoom 8 --max-zoom 10
        done < $WORK_FILE
        rm $WORK_FILE
        echo -n > $INPUT_FILE
        echo "All tiles treated!"
    fi
    sleep 30
done
