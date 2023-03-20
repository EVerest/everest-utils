FROM maven:3.6.1-jdk-11

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /steve

ENV DOCKERIZE_VERSION v0.19.0
RUN curl -sfL https://github.com/powerman/dockerize/releases/download/"$DOCKERIZE_VERSION"/dockerize-`uname -s`-`uname -m` | install /dev/stdin /usr/local/bin/dockerize

RUN wget -qO- https://github.com/RWTH-i5-IDSG/steve/archive/steve-3.4.5.tar.gz | tar xz --strip-components=1
COPY main.properties src/main/resources/config/docker
COPY init.sh .
COPY keystore.jks .

CMD /steve/init.sh
