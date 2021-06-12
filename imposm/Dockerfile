FROM debian:bullseye-slim

RUN apt update && apt install --no-install-recommends -y axel wget postgresql-client ca-certificates && apt clean

ARG IMPOSM3_VERSION=0.11.1
ARG IMPOSM3_TARFILE="imposm-${IMPOSM3_VERSION}-linux-x86-64.tar.gz"
ARG IMPOSM3_BASE_URL="https://github.com/omniscale/imposm3/releases/download/v${IMPOSM3_VERSION}/${IMPOSM3_TARFILE}"

RUN cd /tmp/ && \
    wget -q --no-check-certificate $IMPOSM3_BASE_URL && \
    dir=$(tar -tf $IMPOSM3_TARFILE | head -n1) && \
    tar xzf $IMPOSM3_TARFILE && \
    cd $dir && \
    mv imposm /usr/bin/imposm && \
    mv lib/* /usr/lib && \
    cd / && \
    rm /tmp/$IMPOSM3_TARFILE && \
    rm -r /tmp/$dir && \
    chmod +x /usr/bin/imposm

RUN mkdir /app
RUN mkdir /config

COPY config.json /config
COPY mapping.json /config
COPY entrypoint.sh /
COPY wait-for-it.sh /

ENV POSTGRES_ADDRESS=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=gis

ENV REGIONS=""

WORKDIR /data

RUN adduser --disabled-password --no-create-home --gecos '' batimap

ENTRYPOINT ["/entrypoint.sh"]
