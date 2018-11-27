#!/bin/sh -x

POSTGRES_PORT=${POSTGRES_PORT:-5432}

count=$(PGPASSWORD=$POSTGRES_PASSWORD psql -qtA -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c "SELECT count(*) FROM city_stats where date like '20%'")
result=$?

# initialize database if no record can be found
if [ $result != 0 ] || [ "$count" -lt 10 ]; then
    flask initdb
fi

# start the backend
gunicorn -b ':5000' -w 4 app:app
