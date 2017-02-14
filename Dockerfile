FROM frolvlad/alpine-glibc:alpine-3.4
MAINTAINER Jonathan Hosmer <jonathan@wink.com>

ENV VERSION=0.14.22 \
    SHA1=c43fa0d750e8347ec466ce165053db3cd3dc2fe0

RUN mkdir /opt
RUN apk --no-cache add \
    curl \
    tini \
    pwgen \
    'python=2.7.12-r0' \
    'py-pip=8.1.2-r0' \
  && rm -rf /etc/apk/cache

RUN pip install requests

RUN curl -sSL https://www.factorio.com/get-download/$VERSION/headless/linux64 \
        -o /tmp/factorio_headless_x64_$VERSION.tar.gz && \
    echo "$SHA1  /tmp/factorio_headless_x64_$VERSION.tar.gz" | sha1sum -c && \
    tar xzf /tmp/factorio_headless_x64_$VERSION.tar.gz --directory /opt && \
    rm /tmp/factorio_headless_x64_$VERSION.tar.gz

RUN ln -s /factorio/saves /opt/factorio/saves && \
    ln -s /factorio/mods /opt/factorio/mods

VOLUME /factorio

EXPOSE 34197/udp 27015/tcp

COPY entrypoint.sh /
COPY update.py /
COPY mods /factorio/mods

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/entrypoint.sh"]
