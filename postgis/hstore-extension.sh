#!/bin/bash
set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Load hstore into both template_database and $POSTGRES_DB
for DB in template_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	psql --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS hstore;
EOSQL
done
