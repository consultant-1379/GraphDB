#!/bin/bash -eu

# removing file to avoid concatenation of parameters
rm -f /var/tmp/neo4jExtra.conf
# creating file
touch /var/tmp/neo4jExtra.conf

# assigning config variables based on deployment type
# xl deployment
if [ $DEPLOYMENT_TYPE == "extraLarge_instance_enm" ];then
   printf "dbms.memory.heap.max_size=24g\ndbms.memory.heap.initial_size=24g\ndbms.memory.pagecache.size=70g\n" > /var/tmp/neo4jExtra.conf
fi
