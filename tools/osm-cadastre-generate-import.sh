#!/bin/bash -e

red='\033[0;31m'
green='\033[0;32m'
reset='\033[0m'
info() {
    echo -e "$green$@$reset"
}
workdir="$(dirname "$0")/../data"
test -d "$workdir" || mkdir -p "$workdir"
cd "$workdir"

for insee in "$@"; do
    department="$(echo $insee | sed -E 's/([0-9]{2,3})[0-9]{3}/\1/g')"
    if [ ${#department} = 2 ]; then
        department="0$department"
    fi

    if [ ! -f stats/$department-list.txt ]; then
        wget -O stats/$department-list.txt http://cadastre.openstreetmap.fr/data/$department/$department-liste.txt
    fi

    if [ $# = 0 ]; then
        info "$0 <insee>"
        exit 1
    fi

    if [[ ! "$insee" =~ [0-9] ]]; then
        info "${red}Invalid insee code? '$1'"
        continue
    fi

    insee_3lastdigit="$(echo $insee | sed -E 's/[0-9]{2,3}([0-9]{3})/\1/g')"
    result=$(grep -E "[A-Z0-9]{2}$insee_3lastdigit" stats/$department-list.txt)
    ville=$(echo $result| cut -d ' ' -f2)-$(echo $result | cut -d '"' -f2)

    raster=26012,26013,26015,26016,26018,26019,26022,26025,26026,26027,26029,26030,26036,26043,26044,26046,26047,26048,26050,26053,26055,26066,26067,26069,26076,26080,26082,26089,26090,26091,26104,26105,26109,26112,26120,26122,26123,26126,26127,26130,26132,26136,26142,26147,26150,26151,26152,26153,26154,26158,26161,26168,26175,26178,26180,26181,26183,26186,26187,26188,26189,26190,26195,26199,26200,26201,26204,26205,26209,26215,26227,26228,26229,26230,26233,26234,26236,26237,26238,26239,26242,26244,26245,26246,26248,26253,26254,26255,26256,26260,26262,26265,26266,26267,26269,26274,26279,26280,26282,26283,26286,26289,26291,26296,26299,26304,26306,26308,26318,26321,26327,26328,26329,26340,26354,26359,26361,26363,26366,26369,26370,26371,26372,26374,26375,26376,26377,26378,26383,26384
    echo $ville

    if [ -z "$insee" ] || [ -z "$ville" ]; then
        info "${red}Invalid code? insee='$1', ville='$ville'"
        continue
    elif [[ ",$raster," =~ ",$insee," ]]; then
        info "${red}IS RASTER"
        continue
    fi
    info "Downloading $insee - $ville…"

    curl 'http://cadastre.openstreetmap.fr/' \
        -H 'Host: cadastre.openstreetmap.fr' \
        -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0' \
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
        -H 'Accept-Language: fr,en-US;q=0.7,en;q=0.3' \
        --compressed \
        -H 'Referer: http://cadastre.openstreetmap.fr/' \
        -H 'DNT: 1' \
        -H 'Connection: keep-alive' \
        -H 'Upgrade-Insecure-Requests: 1' \
        --data "dep=$department&ville=$ville&recherche_ville=$insee&bis=true&type=bati&force=false" > /dev/null

    wget "http://cadastre.openstreetmap.fr/data/$department/${ville}.tar.bz2"
done