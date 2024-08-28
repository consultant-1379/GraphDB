ARG ERIC_ENM_SLES_BASE_IMAGE_NAME=eric-enm-sles-base
ARG ERIC_ENM_SLES_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-enm
ARG ERIC_ENM_SLES_BASE_IMAGE_TAG=1.64.0-17

FROM ${ERIC_ENM_SLES_BASE_IMAGE_REPO}/${ERIC_ENM_SLES_BASE_IMAGE_NAME}:${ERIC_ENM_SLES_BASE_IMAGE_TAG}

ARG BUILD_DATE=unspecified
ARG IMAGE_BUILD_VERSION=unspecified
ARG GIT_COMMIT=unspecified
ARG ISO_VERSION=unspecified
ARG RSTATE=unspecified

LABEL \
com.ericsson.product-number="CXC Placeholder" \
com.ericsson.product-revision=$RSTATE \
enm_iso_version=$ISO_VERSION \
org.label-schema.name="ENM Neo4j container" \
org.label-schema.build-date=$BUILD_DATE \
org.label-schema.vcs-ref=$GIT_COMMIT \
org.label-schema.vendor="Ericsson" \
org.label-schema.version=$IMAGE_BUILD_VERSION \
org.label-schema.schema-version="1.0.0-rc1"

RUN groupadd -g 7474 neo4j
RUN useradd -u 7474 -g 7474 -m -s /usr/bin/bash neo4j
RUN echo 'neo4j  ALL=(ALL)   NOPASSWD:ALL' >> /etc/sudoers
RUN echo "root  ALL = NOPASSWD: /bin/su ALL" >> /etc/sudoers
# RPMS INSTALLATION
RUN zypper --non-interactive install python3-six python3-pip sysstat && \
    zypper --non-interactive --no-gpg-checks install EXTRjdk11_CXP9038676 && \
    zypper --non-interactive --no-gpg-checks install ERICneo4j4server_CXP9038634 && \
    zypper --non-interactive --no-gpg-checks install ERICneo4jutilities_CXP9034750 && \
    pip3 uninstall -y PyYAML lxml paramiko netaddr pexpect pytz Jinja2 decorator && \
    zypper --non-interactive install python3-PyYAML python3-lxml python3-paramiko python3-netaddr && \
    zypper --non-interactive install python3-pexpect python3-pytz python3-Jinja2 python3-decorator

# NEO4JUTILITIES CLEANUP
RUN rm -f /opt/ericsson/neo4j/scripts/*pyo && \
    rm -f /opt/ericsson/neo4j/scripts/*pyc

# FIX PERMISSIONS
RUN chown -R neo4j:neo4j /etc/neo4j/ && \
    chmod -R 755 /etc/neo4j/ && \
    chown -R neo4j:neo4j /opt/ericsson/neo4j && \
    chown -R neo4j:neo4j /opt/ericsson/pyu && \
    chown -R neo4j:neo4j /var/lock && \
    chown -R neo4j:neo4j /run/lock && \
    chown neo4j:neo4j /proc/1/fd/1 && \
    ln -s /data /ericsson/3pp/neo4j/data

# COPY AND SETUP NEO4J SERVICE / HEALTH CHECK / ENTRYPOINT SCRIPTS
COPY Docker/image_content/service/ /opt/ericsson/neo4j/service/
RUN chown neo4j:neo4j /ericsson/3pp/neo4j/conf/ && \
    chmod 755 /opt/ericsson/neo4j/service/is_healthy.py && \
    chmod 755 /opt/ericsson/neo4j/service/is_started.py && \
    chmod 755 /opt/ericsson/neo4j/service/entrypoint.py && \
    chmod 755 /opt/ericsson/neo4j/service/generate_conf.py && \
    chmod 755 /opt/ericsson/neo4j/service/stop.py

# COPY AND SETUP STDOUT REDIRECT / PIPE_FIFO
RUN mkdir /content
COPY Docker/image_content/eric-log-libstdout-redirect-golang-cxa30176-1.35.0.x86_64.tar /content/eric-log-libstdout-redirect-golang-cxa30176-1.35.0.x86_64.tar
COPY Docker/image_content/pipe_fifo.sh /usr/local/bin/pipe_fifo.sh

RUN tar -C / -xvf /content/eric-log-libstdout-redirect-golang-cxa30176-1.35.0.x86_64.tar  && \
    rm -rf /content && \
    chmod 755 /usr/local/bin/pipe_fifo.sh

ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

USER neo4j

ARG NEO4J_HOME=/ericsson/3pp/neo4j
RUN echo ". ${NEO4J_HOME}/conf/neo4j_env" >> /home/neo4j/.bashrc

WORKDIR ${NEO4J_HOME}

ENTRYPOINT ["/usr/local/bin/pipe_fifo.sh", "/tini", "-s", "-g", "--", "/opt/ericsson/neo4j/service/entrypoint.py"]
