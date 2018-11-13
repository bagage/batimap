FROM debian:sid-slim

RUN apt update && apt install --no-install-recommends -y axel postgresql-client && apt clean

ARG IMPOSM_URL="https://github.com/omniscale/imposm3/releases/download/v0.6.0-alpha.4/imposm-0.6.0-alpha.4-linux-x86-64.tar.gz"
ARG IMPOSM_TARFILE="imposm-0.6.0-alpha.4-linux-x86-64.tar.gz"

ADD $IMPOSM_URL /tmp
RUN cd /tmp/ && \
    dir=$(tar --exclude="*/*" -tf $IMPOSM_TARFILE) && \
    tar xzf $IMPOSM_TARFILE && \
    cd $dir && \
    mv imposm /usr/bin/imposm && \
    mv lib/* /usr/lib && \
    cd / && \
    rm /tmp/$IMPOSM_TARFILE && \
    rm -r /tmp/$dir && \
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
