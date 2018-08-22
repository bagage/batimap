FROM debian:testing-slim

RUN apt update && \
    apt install -yy postgresql postgresql-client osmctools osmium-tool && \
    apt clean

ENTRYPOINT ["/entrypoint.sh"]
