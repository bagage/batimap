FROM debian
RUN apt update && \
    apt install -y curl jq unzip postgresql-client && \
    apt autoremove && apt clean

ARG VERSION="latest"
ARG FILE="tegola_linux_amd64.zip"

RUN curl -L -H 'Accept:application/octet-stream' \
    `curl -H "Accept: application/vnd.github.v3.raw" -s https://api.github.com/repos/go-spatial/tegola/releases/$VERSION | jq -r ".assets | map(select(.name == \"$FILE\"))[0].browser_download_url"` --output /tmp/$FILE && \
    unzip /tmp/$FILE -d /usr/bin && \
    rm /tmp/$FILE && \
    chmod +x /usr/bin/tegola

ADD config.toml /app/config.toml

COPY wait-for-it.sh /

ENV CONFIG=/app/config.toml

CMD tegola --config $CONFIG serve
