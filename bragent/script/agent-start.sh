#!/bin/bash -eu

if [ "${RESTORE_STATE}" == "ongoing" ]; then
  echo "Restore state detected. Skipping Neo4j startup"
  touch /ericsson/3pp/neo4j/disable-neo4j-healthcheck
  exit 0
fi

/opt/ericsson/scripts/neo4j-start.sh
