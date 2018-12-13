FROM debian
RUN apt update && \
    apt install -y unzip postgresql-client wget && \
    apt autoremove && apt clean

ARG VERSION="v0.8.1"
ARG FILE="tegola_linux_amd64.zip"

RUN wget https://github.com/go-spatial/tegola/releases/download/$VERSION/$FILE -O /tmp/$FILE && \
    unzip /tmp/$FILE -d /usr/bin && \
    rm /tmp/$FILE && \
    chmod +x /usr/bin/tegola

ADD config.toml /app/config.toml

COPY wait-for-it.sh /

ENV CONFIG=/app/config.toml

CMD tegola --config $CONFIG serve
