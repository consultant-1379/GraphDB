#!/bin/bash -eu

BASE_DIR="$(dirname "$0")"
source "${BASE_DIR}/common.sh"

/opt/ericsson/scripts/health-check.sh

touch /ericsson/3pp/neo4j/disable-neo4j-healthcheck

. /ericsson/3pp/neo4j/conf/neo4j_env

# Handle error to enable HC again
function handle_err {
  rm "${INCONSISTENCIES_FOUND_FILE}"
  # healthcheck should be re-enabled by the backup_cleanup.py script
  # then the hook calls it...
  exit 1
}
trap 'handle_err' ERR

readonly NSP=$(python3 -c "from neo4jlib.client.base import LocalNeo4jClient; from neo4jlib.client.auth.credentials import credentials; from pyu.decor.misc import retry_if_fail; print(retry_if_fail(10, 30)(lambda: credentials(LocalNeo4jClient()).admin.password)())")
retcode=$?
if [ ${retcode} -ne 0 ]; then
    printf "\nFailed to obtain neo4j password: ${NSP}\n"
    exit 1
fi

echo "Waiting for neo4j RR to become available"
COUNTER=720
until [[ $(curl --output /dev/null --silent --fail -m 18 --head -u neo4j:${NSP:-neo4j} http://localhost:7474/db/system/cluster/available;echo $?) -eq 0 || $COUNTER -lt 1 ]];
do
    printf '.'
    sleep 5
    let COUNTER-=1
done

echo "Checking if neo4j RR is healthy"
curl --silent -u neo4j:${NSP:-neo4j} http://localhost:7474/db/system/cluster/status | grep -q '\"healthy\":true'

# Create the array of server addresses
coreServers=(${NEO4J_causal__clustering_initial__discovery__members//,/ })

LEADER=""
for address in "${coreServers[@]}"
do
    # Split the address in two parts (host port)
    addrParts=(${address/:/ })

    if curl --silent --fail -u neo4j:${NSP:-neo4j} http://${addrParts[0]}:7474/db/system/cluster/writable; then
        LEADER=${addrParts[0]}
    fi
done

function lastTxId () {
  curl --silent -u neo4j:${NSP:-neo4j} -X POST \
  http://$1:7474/db/data/transaction/commit \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -d '{
  "statements" : [ {
    "statement" : "call dbms.queryJmx(\"org.neo4j:instance=kernel#0,name=Transactions\") yield attributes return attributes[\"LastCommittedTxId\"][\"value\"]"
  } ]
}
' | sed -n 's/.*\"row\":\[\([0-9]*\)\].*$/\1/p' # Extract the value from the json result ..."row":[999]...
}

LEADER_LAST_TXID=$(lastTxId $LEADER)
RR_LAST_TXID=$(lastTxId localhost)
echo "Leader Last Transaction Id: $LEADER_LAST_TXID"
echo "Read Replica last received Transaction Id: $RR_LAST_TXID"

if [ "$pre_backup_synchronization_enabled" = true ] ; then
    sync_start_time=$SECONDS
    timeout "${PRE_BACKUP_REPLICA_SYNC_TIMEOUT}" java -cp :/opt/ericsson/replica-sync-agent/neo4j/lib/* com/ericsson/graphdb/ReplicaSyncChecker
    returncode=$?
    if [ $returncode -eq 0 ]; then
        echo "INFO: Read replica is in sync with Leader after $(( SECONDS - sync_start_time )) seconds"
    else
        echo "ERROR: Read replica is not synchronized with Leader after $(( SECONDS - sync_start_time )) seconds, exiting without proceeding with backup"
        exit 1
    fi
fi

if [[ "$consistency_check_enabled" = true && "$BACKUP_TYPE" != "ROLLBACK" ]]; then
    echo "INFO: Running Read Replica Consistency Check"
    if [ -z "$NEO4J_dbms_default__database" ]; then
      echo "ERROR: Default database is not set."
      exit 1
    fi
    neo4j_consistency_check
else
   if [[ "$BACKUP_TYPE" = "ROLLBACK" ]]; then
       echo "INFO: Skipping Read Replica Consistency Check because BACKUP_TYPE is ROLLBACK"
   fi
   echo "INFO: Stopping Read Replica"
   /ericsson/3pp/neo4j/bin/neo4j stop
fi
