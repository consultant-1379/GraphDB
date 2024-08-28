#!/bin/bash
# Returns the following values:
# NAMESPACE Current NAMESPACE executing the scripts
# RELEASE_NAME Current NEO$J Release name
# NEO4J_SECRET_PASSWORD uncrypted password for NEO4J default user neo4j
if [ "$#" -lt 1 ]; then
   NAMESPACE=$(kubectl config view --minify | grep namespace | awk '{print $2}')
else
   NAMESPACE=$1
fi
RELEASE_NAME=${RELEASE_NAME:-eric-data-graph-database-nj}
NEO4J_SECRET_PASSWORD=${NEO4J_SECRET_PASSWORD:-$(kubectl get secret -n ${NAMESPACE} $RELEASE_NAME-secrets -o jsonpath='{.data.neo4j-password}' | base64 --decode)}
