#!/bin/bash
#*******************************************************************************
#* COPYRIGHT Ericsson 2021
#*
#* The copyright to the computer program(s) herein is the property of
#* Ericsson Inc. The programs may be used and/or copied only with written
#* permission from Ericsson Inc. or in accordance with the terms and
#* conditions stipulated in the agreement/contract under which the
#* program(s) have been supplied.
#*******************************************************************************

BASE_DIR="$(dirname "$0")"
source "${BASE_DIR}/common.sh"

# Handle exit to enable HC again if inconsistencies are not found
function handle_exit {
    if [ -f "${INCONSISTENCIES_FOUND_FILE}" ]; then
        echo "ERROR: Inconsistencies have been found of the Read Replica Neo4j Database. Neo4j will not be started and health-check will not be re-enabled"
        rm -f "${INCONSISTENCIES_FOUND_FILE}"
    else
        echo "INFO: Starting Neo4j and enabling Health-check on Read Replica after Consistency Check"
        /opt/ericsson/scripts/neo4j-start.sh
        rm -f "${HEALTHCHECK_DISABLED_FILE}"
        echo "INFO: Waiting for 1 minute..."
        sleep 1m
        validate_replica_is_synced
    fi
}
trap 'handle_exit' EXIT

. /ericsson/3pp/neo4j/conf/neo4j_env
/ericsson/3pp/neo4j/bin/neo4j status | grep -q "Neo4j is running"
retCode=$?
if [ $retCode -ne 0 ]; then
  echo "WARNING: Aborting Consistency Check process because Neo4j is currently not running, it is possible that a separate backup or Consistency Check process is ongoing"
  exit $retCode
fi

validate_replica_is_synced
retCode=$?
if [ $retCode -eq 0 ]; then
    echo "INFO: Read replica is in sync with Leader"
else
    echo "ERROR: Read replica is not synchronized with Leader after, exiting without proceeding with the consistency check"
    exit 1
fi

# Disable healthcheck before starting Consistency Check
touch "${HEALTHCHECK_DISABLED_FILE}"

neo4j_consistency_check
retCode=$?

exit ${retCode}
