#!/bin/bash -eu

touch /ericsson/3pp/neo4j/disable-neo4j-healthcheck

# Handle exit to enable HC again
function handle_exit {
  rm -f /ericsson/3pp/neo4j/disable-neo4j-healthcheck
}
trap 'handle_exit' EXIT

HOSTNAME=$(hostname -A | awk '{print $1}' | xargs)  # the use of | xargs is to trim the string
export NEO4J_causal__clustering_transaction__advertised__address=${HOSTNAME}:$NEO4J_TX_PORT
export NEO4J_causal__clustering_discovery__advertised__address=${HOSTNAME}:$NEO4J_DISCOVERY_PORT
export NEO4J_causal__clustering_raft__advertised__address=${HOSTNAME}:$NEO4J_RAFT_PORT

export NEO4J_dbms_security_auth__enabled=true
export NEO4J_dbms_tx__log_rotation_retention__policy="5 files"

readonly NSP=$(python3 -c "from neo4jlib.client.base import LocalNeo4jClient; from neo4jlib.client.auth.credentials import credentials; from pyu.decor.misc import retry_if_fail; print(retry_if_fail(10, 30)(lambda: credentials(LocalNeo4jClient()).admin.password)())")
retcode=$?
if [ ${retcode} -ne 0 ]; then
    printf "\nFailed to obtain neo4j password: ${NSP}\n"
    exit 1
fi

# This is a temporary workaround for an issue with read replica not starting if all core servers are not up and running. Currently under investigation
echo "Waiting until core servers are available"
coreServers=(${NEO4J_causal__clustering_initial__discovery__members//,/ })
for address in "${coreServers[@]}"
do
    end="$((SECONDS+${AGENT_NEO4J_REPLICA_START_TIMEOUT_MINS:-60}*60))"
    # Split the address in two parts (host port)
    addrParts=(${address/:/ })
    printf "\nWaiting for ${addrParts[0]}"
    until curl --output /dev/null --silent --fail -u neo4j:${NSP:-neo4j} http://${addrParts[0]}:7474/db/system/cluster/available
    do
        [[ "${SECONDS}" -ge "${end}" ]] && printf "\nError: Timed out waiting .\n" && exit 1
        printf '.'
        sleep 5
    done
done

printf "\nMaking /data/logs directory\n"
mkdir -p "/data/logs"

printf "\nMaking /data/metrics directory\n"
mkdir -p "/data/metrics"

function rr_data_cleanup_if_high_usage_and_lag {( set -e
    data_used_perc=$(df /data | awk '{ print $5 }' | tail -n 1 | cut -d% -f 1)
    if [ "${data_used_perc}" -lt "40" ]; then
        printf "  /data file system usage is %s%%<40%%\n" "${data_used_perc}"
        return
    fi
    printf "  /data file system usage is %s%%>40%%\n" "${data_used_perc}"
    if [ ! -d /data/transactions ]; then
        printf "  directory /data/transactions does not exist\n"
        return
    fi
    if [ ! -d /data/transactions/dps ]; then
        printf "  directory /data/transactions/dps does not exist\n"
        return
    fi
    last_rr_tx_timestamp=$(ls -t --full-time /data/transactions/dps/ | tail -n 1 | awk '{ print $6,$7 }')
    printf "  The last RR tx timestamp is '%s'\n" "${last_rr_tx_timestamp}"
    tenth_oldest_leader_tx_timestamp=$(curl -s -X GET -m 2 "http://consul:8500/v1/kv/enm/deployment/databases/neo4j/tenth_oldest_leader_tx_timestamp?raw=true&stale=true")
    printf "  The tenth oldest leader tx timestamp is '%s'\n" "${tenth_oldest_leader_tx_timestamp}"
    if [[ "${last_rr_tx_timestamp}" < "${tenth_oldest_leader_tx_timestamp}" ]]; then
        printf "    The current RR instance seem to be way behind the leader, as the last transaction timestamp %s < %s (tenth oldest leader tx timestamp).\n" "${last_rr_tx_timestamp}" "${tenth_oldest_leader_tx_timestamp}"
        printf "    Removing /data/databases/*\n"
        rm -rf /data/databases/*
        printf "    Removing /data/transactions/*\n"
        rm -rf /data/transactions/*
    else
        printf "    No need for /data cleanup\n"
    fi
)}

set +e
. /ericsson/3pp/neo4j/conf/neo4j_env
/ericsson/3pp/neo4j/bin/neo4j status
retcode=$?
if [ ${retcode} -eq 0 ]; then
    printf "\nNeo4j is already running...\n"
else
    printf "\nChecking if the /data filesystem usage is over 40%% and the current RR instance is behind way behind the leader.\n"
    rr_data_cleanup_if_high_usage_and_lag
    retcode=$?
    if [ $retcode -ne 0 ]; then
        printf '\nERROR: failed to run bash function rr_data_cleanup_if_high_usage_and_lag. Continuing anyway...\n'
    fi
fi
set -e

printf "\nStarting Neo4j\n"
# Neo4J full path is needed in order to not start in console mode
/opt/ericsson/neo4j/service/entrypoint.py --leave

echo "Waiting until read replica server is available"
end="$((SECONDS+${AGENT_NEO4J_REPLICA_START_TIMEOUT_MINS:-60}*60))"
until curl --output /dev/null --silent --fail --head -u neo4j:${NSP:-neo4j}  http://localhost:7474/db/system/cluster/available
do
    [[ "${SECONDS}" -ge "${end}" ]] && printf "\nError: Neo4J replica start timeout.\n" && exit 1
    printf '.'
    sleep 1
done
printf "\nNeo4j read replica started successfully\n"
