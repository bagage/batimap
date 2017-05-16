#!/bin/bash -e

red='\033[0;31m'
green='\033[0;32m'
reset='\033[0m'
info() {
    echo -e "$green$@$reset"
}

usage() {
    info "${red}usage: $0 department <INSEE|CITY>"
    exit 1
}

workdir="$(dirname "$(realpath $0)")/../data/stats"
test -d "$workdir" || mkdir -p "$workdir" "$workdir"/../ok

if [ "$#" = 0 ]; then
    usage
fi

department=$1
shift
MUNICIPALITY_LIST="$workdir/$department-municipality.txt"
STATISTICS_FILE="$workdir/$department-statistics.csv"

if [ "$#" = 0 ]; then
    info "Scanning for new things…"

    test -d "$workdir/../ok" && to_treat=$(cd "$workdir/../ok" && find . -maxdepth 1 -type d -name 'CL*')

    if [ -z "$to_treat" ]; then
        info "None found."
        usage
    else
        while read commune; do
            insee="$(echo "${commune/.*\/CL/$department}" | cut -d- -f1)"
            OSM_CADASTRE_OVERWRITE=${OSM_CADASTRE_OVERWRITE:-y} \
                "$0" $department $insee && \
                mv "$workdir/../ok/$commune" "$workdir/../ok/done" && sleep 5
        done <<< "$to_treat"
        exit 0
    fi
elif [ "$#" -gt 1 ]; then
    for i in "$@"; do
        "$0" $department $i || exit 1
        [ "$OSM_CADASTRE_OVERWRITE" = y ] && sleep 5
    done
    exit 0
fi

if [ ! -f $MUNICIPALITY_LIST ]; then
    tmp=$(mktemp)
    wget -O $tmp "http://overpass-api.de/api/interpreter?data=[out:csv('ref:INSEE', 'name', ::lat, ::lon;false)];
        relation[boundary='administrative'][admin_level='8']['ref:INSEE'~'$department...'];
        out center;"
    cat $tmp | tr '\t' ',' > $MUNICIPALITY_LIST
    rm $tmp
fi

if [[ "$1" =~ [0-9] ]]; then
    match="^$1,"
else
    match=",$1"
fi
insee=$(grep -i "$match" $MUNICIPALITY_LIST | cut -d',' -f1)
name=$(grep -i "$match" $MUNICIPALITY_LIST | cut -d',' -f2)

if [ -z "$name" ] || [ -z "$insee" ]; then
    info ${red}oops, invalid commune? Skipping $1${reset}
    exit 0
fi

info "Treating $insee - $name…"

department_3digits="$(printf "%03d" $department)"
if [ ! -f "$workdir/$department_3digits-list.txt" ]; then
    wget -O "$workdir/$department_3digits-list.txt" http://cadastre.openstreetmap.fr/data/$department_3digits/$department_3digits-liste.txt
fi

if ! grep -q " .*${insee/$department/}" $workdir/$department_3digits-list.txt; then
    info "$insee/$name is RASTER"
    uniques="\tRASTER"
    relations_count="?"
else
    output="$workdir/results-$insee-$(echo "$name" | tr -c -d [a-zA-Z0-9]).csv"

    if [ -f $output ]; then
        must_download="$OSM_CADASTRE_OVERWRITE"
        if [ -z "$OSM_CADASTRE_OVERWRITE" ]; then
            info "overwrite? (y/N). You can disable with OSM_CADASTRE_OVERWRITE=0"
            read must_download
        fi
    else
        must_download=y
    fi
    if [ "$must_download" = y ]; then
        info "Overpass request for buildings…"
        tmp=$(mktemp)
        wget -O $tmp "http://overpass-api.de/api/interpreter?data=[out:csv('source';false)][timeout:100];
        area[boundary='administrative'][admin_level='8']['ref:INSEE'='$insee']->.searchArea;
        (
          node['building'](area.searchArea);
          way['building'](area.searchArea);
          relation['building'](area.searchArea);
        );
        out;"
        mv $tmp $output
    fi

    if [ ! -f ${output}.relations ]; then
        sleep 1
        info "Overpass request for associated streets…"
        tmp=$(mktemp)
        wget -O $tmp "http://overpass-api.de/api/interpreter?data=[out:csv(::id,::type;false)][timeout:100];
        area[boundary='administrative'][admin_level='8']['ref:INSEE'='$insee']->.searchArea;
        (
            way[building](area.searchArea);
            node(w)['addr:housenumber'];
        );
        out;"
        grep 'node' $tmp > "${output}.relations" || touch "${output}.relations"
    fi

    uniques="$(sort $output | uniq -c | sort -rn | sed -E 's/^[[:space:]]*([0-9]*)[[:space:]]*(.*)$/\1\t\2/g')"
    relations_count=$(wc -l < ${output}.relations)
    for to_remove in \
        "cadastre-dgi-fr source : Direction Générale des Finances Publiques - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction Générale des Impôts - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction Générale des Impôts - Cadastre ; mise à jour :" \
        "extraction vectorielle v1 cadastre-dgi-fr source : Direction Générale des Impôts - Cadas. Mise à jour :" \
        "Direction Générale des Finances Publiques - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction G�n�rale des Imp�ts - Cadastre ; mise � jour :" \
    ; do
        uniques=$(echo "$uniques" | sed "s/$to_remove//gI")
    done
    echo "$uniques" > "$output".stats
fi

[ -f $STATISTICS_FILE ] && sed -i "/^$insee\t$name\t/d" $STATISTICS_FILE
printf "$(grep "^$insee," "$MUNICIPALITY_LIST" | tr ',' '\t')\t$(echo "$uniques" | head -n1)\t$(echo "$relations_count")\n" >> $STATISTICS_FILE
sort -o $STATISTICS_FILE $STATISTICS_FILE
grep -Pq "1NSEE\tNOM\tLAT\tLON\tCOUNT\tDATE\tASSOCIATEDSTREET" $STATISTICS_FILE || sed -i "1 i1NSEE\tNOM\tLAT\tLON\tCOUNT\tDATE\tASSOCIATEDSTREET" $STATISTICS_FILE

info "Treatment done!\n\nSummary:\n$(head -n1 $STATISTICS_FILE)\n$(grep "^$insee" $STATISTICS_FILE)\n\n"

# also regenerate the geojson
"$(dirname "$(realpath $0)")/osm-cadastre-umap-csv2geojson.py" $department
