#!/bin/bash
#*******************************************************************************
#* COPYRIGHT Ericsson 2023
#*
#* The copyright to the computer program(s) herein is the property of
#* Ericsson Inc. The programs may be used and/or copied only with written
#* permission from Ericsson Inc. or in accordance with the terms and
#* conditions stipulated in the agreement/contract under which the
#* program(s) have been supplied.
#*******************************************************************************

readonly REPORT_DIR="/ericsson/3pp/neo4j/data/"
readonly INCONSISTENCIES_FOUND_FILE="/ericsson/3pp/neo4j/inconsistencies-reported"
readonly HEALTHCHECK_DISABLED_FILE="/ericsson/3pp/neo4j/disable-neo4j-healthcheck"

readonly _TIMEOUT=/usr/bin/timeout
. /ericsson/3pp/neo4j/conf/neo4j_env
readonly _JAVA=$JAVA_HOME/bin/java


neo4j_consistency_check () {
    source /opt/ericsson/scripts/neo4j-extra.sh

    echo "Proceeding with Consistency Check"
    if [ -z "$NEO4J_dbms_default__database" ]; then
      echo "ERROR: Default database is not set."
      return 3
    fi
    echo "INFO: Stopping Neo4j on Read Replica for Consistency Check"
    . /ericsson/3pp/neo4j/conf/neo4j_env
    /ericsson/3pp/neo4j/bin/neo4j stop
    retCode=$?
    if [ $retCode -ne 0 ]; then
        return $retCode
    fi
    echo "INFO: Running Consistency Check on Read Replica."
    /ericsson/3pp/neo4j/bin/neo4j-admin check-consistency --additional-config=/var/tmp/neo4jExtra.conf --verbose --database=$NEO4J_dbms_default__database --report-dir=$REPORT_DIR
    retCode=$?
    if [ $retCode -eq 0 ]; then
        echo "INFO: Consistency Check completed successfully, no further action required."
    elif [ $retCode -eq 137 ]; then
      echo "ERROR: Neo4j process exited with OutofMemory issues, please check your heap,pageCache memory settings"
      exit $retCode
    elif [ $retCode -eq 1 ]; then
        # Creating a file to indicate that inconsistencies are found
        touch ${INCONSISTENCIES_FOUND_FILE}
        echo "ERROR: Consistency Check failed with inconsistencies reported. If this was the first run then re-run the Consistency Check. Otherwise, refer to the ENM Troubleshooting Guide for actions to be taken based on the report available in $REPORT_DIR directory."
    else
        echo "ERROR: Consistency Check failed before completion, it is possible the process was interrupted."
    fi
    return $retCode
}

validate_replica_is_synced () {
    echo "INFO: Validating that the Read Replica is synchronized with the leader"
    sync_start_time=$SECONDS
    ${_TIMEOUT} ${PRE_BACKUP_REPLICA_SYNC_TIMEOUT} ${_JAVA} -cp :/opt/ericsson/replica-sync-agent/neo4j/lib/* com/ericsson/graphdb/ReplicaSyncChecker
    retCode=$?
    if [ $retCode -eq 0 ]; then
        echo "INFO: Read replica is in sync with Leader after $(( SECONDS - sync_start_time )) seconds"
    else
        echo "ERROR: Read replica is not synchronized with Leader after $(( SECONDS - sync_start_time )) seconds"
        return $retCode
    fi
}
