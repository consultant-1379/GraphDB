import os
import time
import utilprocs
import helm3procs
import graphdb_util
import setup_env


# Set up variables
CHART_NAME = os.environ['baseline_chart_name']
NAMESPACE = os.environ['kubernetes_namespace']

NUMBER_OF_CORE = 3
TIMEOUT_LENGTH = 300

#Values to be injected should be inserted here
GRAPHDB_OPTIONS = {"imageCredentials.repoPath": "aia_snapshots", "brAgent.enabled": "false", "core.numberOfServers": NUMBER_OF_CORE,
                   "config.neo4jPasswordForTest": "Neo4jCenmUserEncryptedPassword:neo4j:demo"}

# Setup environment
setup_env.deploy_graphdb(GRAPHDB_OPTIONS)

# Get db driver
utilprocs.log('------------------------------------------------')
utilprocs.log('Connect to the db and get the driver')
driver = graphdb_util.connectDB(CHART_NAME, NAMESPACE)
session = driver.session()
# Start tests
utilprocs.log('------------------------------------------------')
utilprocs.log('Starting deployment tests')


def setUp():
    graphdb_util.verifyClusterFormed(NUMBER_OF_CORE, TIMEOUT_LENGTH, session)

    session.run(
        "CREATE (JoelS:Person {name:'Joel Silver', born:1952})"
        "CREATE (LanaW:Person {name:'Lana Wachowski', born:1965}) CREATE (Hugo:Person {name:'Hugo Weaving', born:1960})"
        "CREATE (Lilly:Person {name:'Lilly Wachowski', born:1967}) CREATE (Keanu:Person {name:'Keanu Reeves', born:1964})"
        "CREATE (Carrie:Person {name:'Carrie-Anne Moss', born:1967}) CREATE (Laurence:Person {name:'Laurence Fishburne', born:1961})")


def tearDown():
    session.run("MATCH (a) detach DELETE a")
    session.close()
    utilprocs.log('Teardown: Clean up namespace')
    helm3procs.helm_cleanup_namespace(NAMESPACE)


def test_create_node():
    session.run("CREATE (a:Person {name:'Test Entry', born:2019})")
    result = session.run("MATCH (a:Person) RETURN a.name")
    num_of_entries = 0
    for record in result:
        utilprocs.log(record)
        num_of_entries += 1
    utilprocs.log("Number of entries after create is: " +
                  str(num_of_entries) + "\n")
    assert(num_of_entries == 8), "Unexpected length!"
    session.run("MATCH (a:Person {name: 'Test Entry'}) DELETE a")


def test_create_relationship():
    session.run(
        "MATCH (u:Person {name:'Joel Silver'}), (a:Person {name:'Keanu Reeves'}) CREATE (u)-[:KNOWS]->(a)")
    result = session.run(
        "MATCH (u:Person {name: 'Joel Silver'})-[r]-(a) RETURN u, type(r) AS relationship, a")
    for record in result:
        utilprocs.log(record)
        utilprocs.log("\n")
    assert(record["relationship"] == "KNOWS"), "Unexpected relationship type!"


def test_read():
    result = session.run("MATCH (a:Person) RETURN a")
    num_of_entries = 0
    for record in result:
        utilprocs.log(record)
        num_of_entries += 1
    utilprocs.log("Number of entries after read is: " +
                  str(num_of_entries) + "\n")
    assert (num_of_entries == 7), "Unexpected length!"


def test_update():
    session.run("MATCH (a:Person {name: 'Joel Silver'}) SET a.born = 1980")
    result = session.run(
        "MATCH (a:Person {name: 'Joel Silver'}) RETURN a.name, a.born AS born")
    for record in result:
        utilprocs.log(record)
        utilprocs.log("\n")
    assert (record["born"] == 1980), "Year incorrect!"


def test_delete():
    session.run("MATCH (a:Person {name: 'Joel Silver'}) detach DELETE a")
    result = session.run("MATCH (a) RETURN a")
    num_of_entries = 0
    for record in result:
        utilprocs.log(record)
        num_of_entries += 1
    utilprocs.log("Number of entries after delete is: " +
                  str(num_of_entries) + "\n")
    assert (num_of_entries == 6), "Unexpected length!"



