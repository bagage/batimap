#!/bin/sh

# allow the container to be started with `--user`
if [ "$(id -u)" = '0' ]; then
	find . \! -user batimap -exec chown batimap '{}' +
	exec su batimap -- "$0" "$@"
fi

# wait for other containers to be ready
./wait-for-it.sh

if [ $# = 0 ]; then
    POSTGRES_PORT=${POSTGRES_PORT:-5432}

    count=$(PGPASSWORD=$POSTGRES_PASSWORD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "SELECT count(*) FROM city_stats where date like '20%'")
    result=$?

    # create a custom index to check building geometry, it boosts these filters by x5 factor
    PGPASSWORD="$POSTGRES_PASSWORD" psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c 'CREATE INDEX IF NOT EXISTS building_geometrytype ON osm_buildings (st_geometrytype(geometry))'
    PGPASSWORD="$POSTGRES_PASSWORD" psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c 'CREATE INDEX IF NOT EXISTS admin_insee ON osm_admin USING gist (insee gist_trgm_ops)'

    # initialize database if no record can be found
    if [ $result != 0 ] || [ "$count" -lt 10 ]; then
        echo "Batimap will start initializing db..."
        flask initdb
        echo "Batimap initialization done, starting now..."
    else
        echo "Batimap db already setup, cleaning tiles..."
        # create ready file
        touch tiles/initdb_is_done
        # maintenance mode is terminated
        rm -f html/maintenance.html
    fi

    GUNICORN_TIMEOUT_VALUE=${GUNICORN_TIMEOUT_VALUE:=60}
    GUNICORN_WORKERS=${GUNICORN_WORKERS:=4}

    # start the back
    echo "Batimap is ready for use!"
    gunicorn --bind ':5000' --timeout $GUNICORN_TIMEOUT_VALUE --workers $GUNICORN_WORKERS batimap.wsgi:app
else
    exec "$@"
fi
