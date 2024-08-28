import os
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
GRAPHDB_OPTIONS = {"imageCredentials.repoPath": "aia_releases", "brAgent.enabled": "true", "brAgent.backupTypeList": "{RELEASETest}", "core.numberOfServers": NUMBER_OF_CORE,
                   "config.neo4jPasswordForTest": "Neo4jCenmUserEncryptedPassword:neo4j:demo"}

def setUp():
    setup_env.deploy_bro()
    setup_env.deploy_graphdb(GRAPHDB_OPTIONS)
    utilprocs.log('------------------------------------------------')
    utilprocs.log('Starting tests')
    global session
    global driver
    driver = graphdb_util.connectDB(CHART_NAME, NAMESPACE)
    session  = driver.session()

def tearDown():
    utilprocs.log('Teardown: Clean up namespace')
    helm3procs.helm_cleanup_namespace(NAMESPACE)


def test_cluster_formed():
    graphdb_util.verifyClusterFormed(NUMBER_OF_CORE+1, TIMEOUT_LENGTH, session)
    session.close()
