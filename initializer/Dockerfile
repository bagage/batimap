FROM debian:sid-slim

RUN apt update && apt install --no-install-recommends -y axel postgresql-client curl jq ca-certificates && apt clean

# 0 == latest
ARG VERSION="0"
ARG FILE="imposm-latest.tar.gz"

RUN curl -L -H 'Accept:application/octet-stream' \
    `curl -H "Accept: application/vnd.github.v3.raw" -s https://api.github.com/repos/omniscale/imposm3/releases | jq -r ".[0].assets[0].browser_download_url"` --output /tmp/$FILE && \
    cd /tmp && \
    dir=$(tar --exclude="*/*" -tf $FILE) && \
    tar xzf $FILE && \
    cd $dir && \
    mv imposm /usr/bin/imposm && \
    mv lib/* /usr/lib && \
    cd / && \
    rm /tmp/$FILE && \
    chmod +x /usr/bin/imposm

RUN mkdir /app

COPY config.json /app
COPY mapping.json /app
COPY import_from_geofabrik.sh /
COPY wait-for-it.sh /

RUN chmod +x /import_from_geofabrik.sh

ENV POSTGRES_ADDRESS=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis

ENV REGIONS=""

ENTRYPOINT ["bash", "-c", "/import_from_geofabrik.sh $REGIONS"]
