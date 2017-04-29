#!/bin/bash -e

red='\033[0;31m'
green='\033[0;32m'
reset='\033[0m'
info() {
    echo -e "$green$@$reset"
}

workdir="$(dirname "$0")/../data/stats"
test -d "$workdir" || mkdir -p "$workdir"
cd "$workdir"

DEPARTMENT_NUMBER='38'
MUNICIPALITY_LIST="$DEPARTMENT_NUMBER-municipality.txt"
STATISTICS_FILE="$DEPARTMENT_NUMBER-statistics.csv"

if [ "$#" = 0 ]; then
    info "Scanning for new things…"
    to_treat=$(find ../ok -maxdepth 1 -type d  -name 'CL*')

    if [ -z "$to_treat" ]; then
        info "$0 <commune>\nou\n$0 <INSEE>\n"
        exit 1
    else
        while read commune; do
            insee="$(echo "${commune/.*\/CL/$DEPARTMENT_NUMBER}" | cut -d- -f1)"
            OSM_CADASTRE_OVERWRITE=${OSM_CADASTRE_OVERWRITE:-y} $0 $insee && mv "$commune" ../ok/done && sleep 5
        done <<< "$to_treat"
        exit 0
    fi
elif [ "$#" -gt 1 ]; then
    for i in "$@"; do
        $0 $i || exit 1
        [ "$OSM_CADASTRE_OVERWRITE" = y ] && sleep 5
    done
    exit 0
fi

if [ ! -f $MUNICIPALITY_LIST ]; then
    tmp=$(mktemp)
    wget -O $tmp "http://overpass-api.de/api/interpreter?data=[out:csv('name', 'ref:INSEE';false)];
        relation[boundary='administrative'][admin_level='8']['ref:INSEE'~'26...'];
        out;"
    cat $tmp | tr '\t' ',' > $MUNICIPALITY_LIST
    rm $tmp
fi

if [[ "$1" =~ [0-9] ]]; then
    insee=$1
    skip=26029,26044,26053,26109,26120,26132,26151,26158,26187,26230,26237,26260,26265,26280,26366
    if [[ ",$skip," =~ ",$insee," ]]; then
        info Skipping $insee
        exit 0
    fi
    name=$(grep ",$1$" $MUNICIPALITY_LIST | cut -d',' -f1)
else
    name=$1
    insee=$(grep "^$1," $MUNICIPALITY_LIST | cut -d',' -f2)
fi

if [ -z "$name" ] || [ -z "$insee" ]; then
    info ${red}oops, invalid commune? $1${reset}
    exit 1
fi

info "Treating $insee - $name…"

raster=26012,26013,26015,26016,26018,26019,26022,26025,26026,26027,26029,26030,26036,26043,26044,26046,26047,26048,26050,26053,26055,26066,26067,26069,26076,26080,26082,26089,26090,26091,26104,26105,26109,26112,26120,26122,26123,26126,26127,26130,26132,26136,26142,26147,26150,26151,26152,26153,26154,26158,26161,26168,26175,26178,26180,26181,26183,26186,26187,26188,26189,26190,26195,26199,26200,26201,26204,26205,26209,26215,26227,26228,26229,26230,26233,26234,26236,26237,26238,26239,26242,26244,26245,26246,26248,26253,26254,26255,26256,26260,26262,26265,26266,26267,26269,26274,26279,26280,26282,26283,26286,26289,26291,26296,26299,26304,26306,26308,26318,26321,26327,26328,26329,26340,26354,26359,26361,26363,26366,26369,26370,26371,26372,26374,26375,26376,26377,26378,26383,26384
if [[ ",$raster," =~ ",$insee," ]]; then
    uniques="\tRASTER"
    relations_count="?"
else
    output="./results-$insee-$(echo "$name" | tr -c -d [a-zA-Z0-9]).csv"

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
        info "Overpass request for relations…"
        tmp=$(mktemp)
        wget -O $tmp "http://overpass-api.de/api/interpreter?data=[out:csv('id';false)][timeout:100];
        area[boundary='administrative'][admin_level='8']['ref:INSEE'='$insee']->.searchArea;
        (
          relation[type='associatedStreet'](area.searchArea);
          node['addr:housenumber']['addr:street'](area.searchArea);
        );
        out;"
        mv $tmp "${output}.relations"
    fi

    uniques="$(sort $output | uniq -c | sort -rn | sed -E 's/^[[:space:]]*([0-9]*)[[:space:]]*(.*)$/\1\t\2/g')"
    relations_count=$(wc -l < ${output}.relations)
    for to_remove in \
        "cadastre-dgi-fr source : Direction Générale des Finances Publiques - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction Générale des Impôts - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction Générale des Impôts - Cadastre ; mise à jour :" \
        "extraction vectorielle v1 cadastre-dgi-fr source : Direction Générale des Impôts - Cadas. Mise à jour :" \
        "Direction Générale des Finances Publiques - Cadastre. Mise à jour :" \
        "Direction Générale des Finances Publiques - Cadastre. Mise à jour :" \
        "cadastre-dgi-fr source : Direction G�n�rale des Imp�ts - Cadastre ; mise � jour :" \
    ; do
        uniques=$(echo "$uniques" | sed "s/$to_remove//g")
    done
    echo "$uniques" > "$output".stats
fi

[ -f $STATISTICS_FILE ] && sed -i "/^$insee\t$name\t/d" $STATISTICS_FILE
printf "$insee\t$name\t$(echo "$uniques" | head -n1)\t$(echo "$relations_count")\n" >> $STATISTICS_FILE
sort -o $STATISTICS_FILE $STATISTICS_FILE
grep -Pq "1NSEE\tNOM\tCOUNT\tDATE\tASSOCIATEDSTREET" $STATISTICS_FILE || sed -i "1 i1NSEE\tNOM\tCOUNT\tDATE\tASSOCIATEDSTREET" $STATISTICS_FILE

info "Treatment done!\n\nSummary:\n$(head -n1 $STATISTICS_FILE)\n$(grep $insee $STATISTICS_FILE)"
