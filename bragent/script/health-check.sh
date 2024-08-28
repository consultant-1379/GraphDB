#!/bin/bash -eu

if [ ! -f "/ericsson/3pp/neo4j/disable-neo4j-healthcheck" ]; then
    echo "Checking if RR is listening on http and bolt ports"
    echo * | curl -v telnet://localhost:7687 > /dev/null 2>&1
    var1=$?
    echo * | curl -v telnet://localhost:7474 > /dev/null 2>&1
    var2=$?
    test ${var1} -eq 0 && test ${var2} -eq 0
fi

if [ "${SUB_AGENT_ENABLED:-false}" == "true" ]; then
    echo * | curl -v telnet://localhost:${AGENT_GRPC_SERVER_PORT:-10000}
    var3=$?
    test ${var3} -eq 0
fi
