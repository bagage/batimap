#!/bin/bash -e

SCRIPT_DIR=$(realpath $(dirname $0))
WORK_DIR=/tmp/batimap-init

mkdir -p $WORK_DIR
cd $WORK_DIR

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

for region in $regions; do
    file=$(basename $region).osm.pbf
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf || test -f $file
    axel --no-clobber http://download.geofabrik.de/europe/$region.osm.pbf.md5 || test -f $file.md5
    md5sum -c $file.md5
done


for region in $regions; do
    region=$(basename $region)
    echo "Preparing $region…"
    # only keep administrative boundaries and buildings
    test -f ${region}_boundaries.osm.pbf || osmium tags-filter $region.osm.pbf "type=boundary,boundary=administrative" -o ${region}_boundaries.osm.pbf
    test -f ${region}_buildings.osm.pbf || osmium tags-filter $region.osm.pbf "building" -o ${region}_buildings.osm.pbf
done

echo "Persisting in db…"
test -f boundaries.osm.pbf || osmium merge *_boundaries.osm.pbf -o boundaries.osm.pbf
test -f buildings.osm.pbf || osmium merge *_buildings.osm.pbf -o buildings.osm.pbf
PGPASSWORD=batimap osm2pgsql $option -C 6000Mo -H localhost -U docker -P 5432 \
    --verbose --proj 4326 --database gis boundaries.osm.pbf \
    --style $SCRIPT_DIR/osm2pgsql.style --slim --flat-nodes osm2pgsql.flatnodes
PGPASSWORD=batimap osm2pgsql $option -C 6000Mo -H localhost -U docker -P 5432 \
    --verbose --proj 4326 --database gis --prefix buildings_osm buildings.osm.pbf \
    --style $SCRIPT_DIR/osm2pgsql.style --slim --flat-nodes osm2pgsql.flatnodes
rm osm2pgsql.flatnodes

echo "Imports done! Refreshing stats…"

FLASK_APP=$SCRIPT_DIR/../../backend/app.py flask initdb

echo "All done!"
