#!/bin/bash
# This tests is used to simulate basic load in a neo4j cluster.
# The script identifies each kind of pods and based on that execute diverses Cypher SQL commnads

createData(){
  RNDSTRING="`head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo ''`"
  eval "$1=\"CREATE (a:Artist { Name : '$RNDSTRING' }) \" "
}

readData(){
  eval "$1=\"MATCH (artist:Artist) RETURN artist.Name \" "
}
countData(){
   eval "$1=\"MATCH (n) RETURN count(n)\" "
}
removeData(){
  eval "$1=\"MATCH (n) DETACH DELETE n \" "
}

TOTALINSERT=10
usage() {
  echo "Usage: $0 {-t total} {-n Namespace} {-h help} " 1>&2;
  echo "   t: Total number of Inserts done in neo4j DB, default is $TOTALINSERT inserts"
  echo "   n: NameSpace -- default "
  echo "   r: Release name -- default is eric-data-graph-database-nj"
  echo "   p: Password -- by default it will get from <Relase name>-secrets secret"
  echo ""
  echo "This scripts will insert random data on neo4j and reads the data."
  echo "The script will identify each pod or replica."
  echo "The script will identify the role on each pod."
  echo "The script Will identify the neo4j container (excluding JMX)."
  echo ""
  echo "The inserts are being executed through the \"LEADER\" pod, due the commands are calling directly to the pod."
  echo "Once the information is validated and displayed, the system will drop completely the database."
  exit -1;
}

while getopts ":t:n:r:p:h" o; do
  case "${o}" in
  t)
      # Validates is a numeric data
      if [[ ${OPTARG} =~ ^-?[0-9]+$ ]]; then
        TOTALINSERT=${OPTARG}
      else
        echo "Needs to indicate a valid numeric value"
        exit -2;
      fi
     ;;
  n)
    NAMESPACE=${OPTARG}
    ;;
  r)
    RELEASE_NAME=${OPTARG}
    ;;
  p)
    NEO4J_SECRET_PASSWORD=${OPTARG}
    ;;
  h)
    usage
    ;;
  *)
    usage
    ;;
 esac
done
shift $((OPTIND-1))

if [ -z "${TOTALINSERT}" ]; then
  usage
fi

read -r -p "This test will drop the neo4j db completely, Are you sure you want to proceed? [y/N] " response
SCRIPT_BASENAME="`dirname $0`"
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]
then
    source $SCRIPT_BASENAME/getSettings.sh $NAMESPACE
else
    exit -2;
fi
PODS="`kubectl get pods -o go-template --namespace=$NAMESPACE --template '{{range .items}}{{.metadata.name}}{{","}}{{end}}' -lapp=$RELEASE_NAME  `"
IFS=', ' read -r -a array <<< "$PODS"
if [[ ${#array[@]} -gt 0 ]]; then
     echo "Testing each POD "
     for index in "${!array[@]}"
     do
         POD="${array[index]}"
         CONTAINERS="`kubectl get pod --namespace=$NAMESPACE ${POD} -o=custom-columns=CONTAINERS:.spec.containers[*].name  --no-headers=true`"
         IFS=', ' read -r -a container <<< "$CONTAINERS"
         for idxcont in "${!container[@]}"
         do
           if [[ ${container[idxcont]} != *"jmx"* ]]; then
              CONTAINER="${container[idxcont]}"
              rol=`kubectl exec -it ${array[index]} -c $CONTAINER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD "CALL dbms.cluster.role()" `
              echo $rol
              if [[ $? != 0 ]]; then
                 echo "$0 works in a neo4j cluster environment exclusively"
                 exit 5
              fi
              if [[ "$rol" == *"LEADER"* ]]; then
                 LEADER="$POD"
                 CONTAINERLEADER="$CONTAINER"
                 for (( n=1; n<=$TOTALINSERT; n++ ))
                 do
                     createData DATA
                     COMMAND="kubectl exec -it ${array[index]} -c $CONTAINER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD \"$DATA\" "
                     echo "Executing: $COMMAND"
                     eval $COMMAND
                 done
              elif [[ "$rol" == *"FOLLOWER"* ]]; then
                 readData DATA
                 COMMAND="kubectl exec -it ${array[index]} -c $CONTAINER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD \"$DATA\" "
                 echo "Executing: $COMMAND"
                 eval $COMMAND
              elif [[ "$rol" == *"REPLICA"* ]]; then
                 countData DATA
                 COMMAND="kubectl exec -it ${array[index]} -c $CONTAINER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD \"$DATA\" "
                 echo "Executing: $COMMAND"
                 eval $COMMAND
              fi
           fi
         done
     done
     echo "Removing all data"
     removeData DATA
     COMMAND="kubectl exec -it $LEADER -c $CONTAINERLEADER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD \"$DATA\" "
     echo "Executing: $COMMAND"
     eval $COMMAND
     countData DATA
     COMMAND="kubectl exec -it $LEADER -c $CONTAINERLEADER --namespace=$NAMESPACE -- /ericsson/3pp/neo4j/bin/cypher-shell -u neo4j -p $NEO4J_SECRET_PASSWORD \"$DATA\" "
     echo "Executing: $COMMAND"
     eval $COMMAND
fi
