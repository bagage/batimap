FROM debian
RUN apt update && \
    apt install wget --yes && \
    wget https://github.com/terranodo/tegola/releases/download/v0.3.2/tegola_linux_amd64 && \
    mv tegola_linux_amd64 /usr/bin/tegola && \
    chmod +x /usr/bin/tegola
ADD config.toml /root
CMD sleep 30 && tegola_linux_amd64 -config /root/config.toml
