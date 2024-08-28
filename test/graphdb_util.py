import utilprocs
import time
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable
from neobolt.addressing import AddressError


user = "neo4j"
password = "demo"


def connectDB(chart_name, namespace):
    # Using bolt+routing to allow the service to identify the leader/follower roles based in the bolt request
    host = "neo4j://" + chart_name + "." + namespace + ".svc.cluster.local"
    #host = "bolt+routing://" + chart_name + "." + namespace + ".svc.cluster.local"
    num_retries = 6
    for attempt_no in range(num_retries):
        try:
            utilprocs.log('Trying database driver .. ')
            utilprocs.log('Host is: ' + host)
            return GraphDatabase.driver(host, auth=basic_auth(user=user, password=password), encrypted=False)
        except Exception as error:
            if attempt_no < (num_retries - 1):
                utilprocs.log('Retrying database driver connection ')
                time.sleep(60)
            else:
                raise error

def verifyClusterFormed(expected_core, timeout_length, session):
    num_cores = 0
    timeout = time.time() + timeout_length
    while num_cores < expected_core:
        assert (time.time() < timeout) , "Timed out waiting for cluster formation"
        try:
            result = session.run("CALL dbms.cluster.overview()")
            num_cores = 0
            for core in result:
                num_cores+=1
            utilprocs.log("Number of Core Servers in Cluster: "+str(num_cores))
            time.sleep(5)
        except AddressError as e:
            utilprocs.log( "<p>Cluster is unavailable, retrying: %s</p>" % e)
            time.sleep(5)
