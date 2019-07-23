FROM debian:sid-slim

RUN apt update && apt install --no-install-recommends -y axel postgresql-client && apt clean

ARG IMPOSM_VERSION=0.8.0
ARG IMPOSM_TARFILE="imposm-${IMPOSM_VERSION}-linux-x86-64.tar.gz"
ARG IMPOSM_BASE_URL="https://github.com/omniscale/imposm3/releases/download/v${IMPOSM_VERSION}/${IMPOSM_TARFILE}"

RUN cd /tmp/ && \
    axel -k $IMPOSM_BASE_URL && \
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

ENTRYPOINT ["bash", "-c", "/entrypoint.sh $REGIONS"]
