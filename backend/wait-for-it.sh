#!/usr/bin/env bash

cmdname=$(basename $0)

echoerr() { if [[ $QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $cmdname host:port [-s] [-- command args]
    -h HOST | --host=HOST       Host or IP under test
    -p PORT | --port=PORT       TCP port under test
                                Alternatively, you specify the host and port as host:port
    -s | --strict               Only execute subcommand if the test succeeds
    -q | --quiet                Don't output any status messages
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    echoerr "$cmdname: waiting for postgis to be initialized without a timeout"

    start_ts=$(date +%s)
    while :
    do
        count=`PGPASSWORD=$POSTGRES_PASSWD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "SELECT count(*) FROM planet_osm_polygon"`
        result=$?
        if [[ $result -eq 0 ]]; then
            if [[ $count -gt 0 ]]; then
                end_ts=$(date +%s)
                echoerr "$cmdname: postgis is available after $((end_ts - start_ts)) seconds"
                break
            fi
        fi
        sleep 5
    done
    return $result
}

# process arguments
while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        hostport=(${1//:/ })
        POSTGRES_HOST=${hostport[0]}
        POSTGRES_PORT=${hostport[1]}
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -s | --strict)
        STRICT=1
        shift 1
        ;;
        -h)
        POSTGRES_HOST="$2"
        if [[ $POSTGRES_HOST == "" ]]; then break; fi
        shift 2
        ;;
        --host=*)
        POSTGRES_HOST="${1#*=}"
        shift 1
        ;;
        -p)
        POSTGRES_PORT="$2"
        if [[ $POSTGRES_PORT == "" ]]; then break; fi
        shift 2
        ;;
        --port=*)
        POSTGRES_PORT="${1#*=}"
        shift 1
        ;;
        --user=*)
        POSTGRES_USER="${1#*=}"
        shift 1
        ;;
        --password=*)
        POSTGRES_PASSWD="${1#*=}"
        shift 1
        ;;
        --db=*)
        POSTGRES_DB="${1#*=}"
        shift 1
        ;;
        --)
        shift
        CLI=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$POSTGRES_HOST" == "" || "$POSTGRES_PORT" == "" || "$POSTGRES_USER" == "" || "$POSTGRES_PASSWD" == "" || "$POSTGRES_DB" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

STRICT=${STRICT:-0}
QUIET=${QUIET:-0}

wait_for
RESULT=$?

if [[ $CLI != "" ]]; then
    if [[ $RESULT -ne 0 && $STRICT -eq 1 ]]; then
        echoerr "$cmdname: strict mode, refusing to execute subprocess"
        exit $RESULT
    fi
    eval "${CLI[@]}"
else
    exit $RESULT
fi
