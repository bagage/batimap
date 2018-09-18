FROM debian:sid-slim

RUN apt update && apt install --no-install-recommends -y axel postgresql postgresql-client osmctools osmium-tool osm2pgsql && apt clean

COPY import_from_geofabrik.sh /
COPY osm2pgsql.style /
COPY wait-for-it.sh /

RUN chmod +x /import_from_geofabrik.sh


ENV POSTGRES_ADDRESS=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis

ENV REGIONS=""

ENTRYPOINT ["bash", "-c", "/import_from_geofabrik.sh $REGIONS"]
