# To be improved and use ARGs after slave is upgraded to Docker 17.05+
FROM $GRAPHDB_REPO_PATH:$GRAPHDB_TAG
#FROM armdocker.rnd.ericsson.se/proj_oss_releases/graphdb-base:1.0.1

USER root

# To be improved and use Multistage build after slave is upgraded to Docker 17.05+
COPY bragent.extracted /opt/ericsson/backup-restore-agent/bragent
COPY script /opt/ericsson/scripts/

# Enable fast compression level
ENV ZSTD_CLEVEL=-10

RUN chown -R neo4j:neo4j /opt/ericsson/backup-restore-agent/bragent /opt/ericsson/scripts/ && \
    zypper --non-interactive install zstd curl

COPY target/replica-sync-checker-*.jar /opt/ericsson/replica-sync-agent/neo4j/lib/
COPY target/neo4j-java-driver-*.jar /opt/ericsson/replica-sync-agent/neo4j/lib/
COPY target/reactive-streams-*.jar /opt/ericsson/replica-sync-agent/neo4j/lib/

USER neo4j
# Entrypoint 'tini' is temporary fix to handle SIGCHLD processes. Will need to be removed
# once SIGCHLD handling is implemented in the backup-restore-agent
ENTRYPOINT ["/usr/local/bin/pipe_fifo.sh", "/tini", "-s", "-g", "--", "/opt/ericsson/backup-restore-agent/bragent"]
