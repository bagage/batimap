#!/bin/bash -e

red='\033[0;31m'
green='\033[0;32m'
reset='\033[0m'
info() {
    echo -e "$green$@$reset"
}
workdir="$(dirname "$0")/../data"
test -d "$workdir" || mkdir -p "$workdir/"{stats,ok}

if [ $# = 0 ]; then
    info "$0 <insee>"
    exit 1
fi

for insee in "$@"; do
    department="$(echo $insee | sed -nE 's/([0-9]{2,3})[0-9]{3}/\1/p')"

    if [[ ! "$insee" =~ [0-9] ]] || [ -z "$department" ]; then
        info "${red}Invalid insee code? '$insee'. Expected 26001 or similar."
        continue
    fi

    if [ ${#department} = 2 ]; then
        department="0$department"
    fi

    if [ ! -f "$workdir/stats/$department-list.txt" ]; then
        wget -O "$workdir/stats/$department-list.txt" http://cadastre.openstreetmap.fr/data/$department/$department-liste.txt
    fi

    insee_3lastdigit="$(echo $insee | sed -E 's/[0-9]{2,3}([0-9]{3})/\1/g')"
    result=$(grep -E "[A-Z0-9]{2}$insee_3lastdigit" "$workdir/stats/$department-list.txt" || true)
    ville=$(echo $result| cut -d ' ' -f2)-$(echo $result | cut -d '"' -f2)

    if [ -z "$insee" ] || [ -z "$ville" ]; then
        info "${red}Invalid code? insee='$1', ville='$ville'"
        continue
    elif [ -z "$result" ]; then
        info "${red}$insee is RASTER or UNKNOWN. Ignoring"
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
        --data "dep=$department&ville=$ville&recherche_ville=$insee&bis=true&type=bati&force=false"

    wget "http://cadastre.openstreetmap.fr/data/$department/${ville}.tar.bz2" -O "$workdir/${ville}.tar.bz2"
done
