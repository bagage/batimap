#!/bin/bash -e

cd /home/gautier/code/osm/pbf

if [ $# -gt 0 ]; then
    regions="$@"
else
    regions="france-latest france/guadeloupe-latest france/guyane-latest france/martinique-latest france/mayotte-latest france/reunion-latest"
fi

# for region in $regions; do
#     axel -c http://download.geofabrik.de/europe/$region.osm.pbf || true
#     axel -c http://download.geofabrik.de/europe/$region.osm.pbf.md5 || true
# done

# md5sum -c *.md5

args=()
for region in $regions; do
    args+=('<(osmconvert' $(echo $region | rev | cut -d/ -f1 | rev).osm.pbf '--out-o5m)')
done
eval osmconvert ${args[@]} -o=my-region.o5m

# only keep administrative boundaries and buildings
osmfilter --keep="type=boundary and boundary=administrative or building" -v my-region.o5m -o=boundaries_buildings.osm

# import in database. Warning: it will wipe existing osm_planet_* tables!
osm2pgsql -H localhost -U docker -P 5432 --verbose --proj 4326 --hstore-all -W --database gis boundaries_buildings.osm
