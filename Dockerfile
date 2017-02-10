FROM ubuntu:latest
MAINTAINER Jonathan Hosmer <jonathan@wink.com>

RUN apt update && apt install -y \
        curl

ENV FACTORIO_VERSION=0.14.22

RUN useradd factorio
RUN mkdir -p /opt/factorio/saves && chown -R factorio:factorio /opt/factorio
USER factorio
WORKDIR /opt/factorio

RUN curl -vL "https://www.factorio.com/get-download/${FACTORIO_VERSION}/headless/linux64" -o factorio.tar.gz && \
    tar -zxvf factorio.tar.gz

COPY update.py /opt/factorio

EXPOSE 34197

ENTRYPOINT ["/opt/factorio/factorio/bin/x64/factorio", "--create", "saves/1.zip"]
