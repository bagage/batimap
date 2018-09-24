FROM debian:sid-slim

RUN apt update && apt install --no-install-recommends -y axel postgresql postgresql-client osmctools osmium-tool && apt clean

# compile oms2psql manually for https://github.com/openstreetmap/osm2pgsql/pull/865
RUN apt update \
    && apt install -y git cmake libpq-dev g++ libproj-dev libosmium2-dev \
                      libboost-system-dev libboost-filesystem-dev liblua5.3-dev \
    && apt clean \
    && cd /tmp/ \
    && git clone https://github.com/bagage/osm2pgsql --depth 1 -b drop-old-style-mps \
    && mkdir osm2pgsql/build \
    && cd /tmp/osm2pgsql/build \
    && cmake .. && make install \
    && cd /tmp/ && rm -rf osm2pgsql

COPY import_from_geofabrik.sh /
COPY osm2pgsql.style /
COPY wait-for-it.sh /

RUN chmod +x /import_from_geofabrik.sh

ENV POSTGRES_ADDRESS=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis

ENV REGIONS=""

ENTRYPOINT ["bash", "-c", "/import_from_geofabrik.sh $REGIONS"]
