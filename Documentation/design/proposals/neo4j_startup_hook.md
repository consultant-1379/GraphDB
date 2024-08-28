# [TORF-415313] Deliver 4th instance of Neo4J as a RR part 2

## Overview

The Neo4J RR implementation in cENM needs a final step to enable BUR
functionality.
The backup agent runs as PID 1 on the RR pod since BUR lifecycle events
necessitate restarts of Neo4J and we don't want the pod to be terminated when
that happens.

Therefore a new pre-registration hook has been implemented in backup agent
intended to start Neo4j and run healthchecks before registering with BRO and
indicate that the RR is ready for conducting backups. A startup and healthcheck
script named neo4j-startup.sh has already been implemented as part of
TORF-377431 and TORF-378695.

The scope of this story is implementing the config hook for running that startup
script at agent registration time.

This will require the following changes:

## Helm chart changes

The file neo4j-bragent-deployment.yaml under
GraphDB\Helm\eric-data-graph-database-nj\templates\ will have the "AGENT_REGISTRATION_PRE_CMD"
variable config added:

```yaml
# Configuration variables for taking a backup
  - name: BACKUP_PATHS
    value: "/data/"
  - name: AGENT_REGISTRATION_PRE_CMD
    value: "/neo4j-start.sh"
```

The functionality will be tested by verifying if RR is successfully started by
the agent before registration and needed changes to the startup script will be
implemented.

## Verification of Neo4J RR

The story requires verification of following points:

- RR implementation and successful sync with main cluster. Once the RR has
started, insert queries will be run against core servers using Cyper Shell and
then a read will be done on the RR to check if writes were synced.
- Neo4j agent is ready to take a backup as soon as the pre-reg command
completes. For example the read-replica should be synced with core servers.
- Pod delete to ensure the RR is gracefully stopped, etc.
- Health checks are working and have expected outcomes including gracefully
stopping Neo4j.
