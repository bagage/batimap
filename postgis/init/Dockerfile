FROM debian:sid-slim

RUN apt update
RUN apt install --no-install-recommends -y axel postgresql postgresql-client osmctools osmium-tool osm2pgsql
RUN apt clean

COPY import_from_geofabrik.sh /
COPY osm2pgsql.style /

RUN chmod +x /import_from_geofabrik.sh

ENV POSTGRES_ADDRESS=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis

ENTRYPOINT "/import_from_geofabrik.sh"
