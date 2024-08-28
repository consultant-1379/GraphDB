import os
import subprocess
import time

import helm3procs
import k8sclient
import utilprocs

import broapi
import graphdb_util
import setup_env

SCOPE = "BURTest"
BACKUP_NAME = 'TestBackup'
ACTION_TIMEOUT = 2100
AGENT_TIMEOUT = 600
AGENT_ID = 'eric-data-graph-database-nj-bragent'
NUMBER_OF_CORE = 3
CLUSTER_TIMEOUT_LENGTH = 300

CHART_NAME = os.environ['baseline_chart_name']
NAMESPACE = os.environ['kubernetes_namespace']
GRAPHDB_RELEASE = f'{CHART_NAME}-{NAMESPACE}'[:53]
GRAPHDB_OPTIONS = {"brAgent.enabled": "true", "brAgent.backupTypeList": "{BURTest}", "imageCredentials.repoPath": "aia_snapshots", "core.numberOfServers": NUMBER_OF_CORE,
                   "config.neo4jPasswordForTest": "Neo4jCenmUserEncryptedPassword:neo4j:demo"}

BRO = broapi.Bro(host='eric-ctrl-bro', port='7001')


def setup():
    try:
        utilprocs.log('Test setup')
        setup_env.deploy_bro()
        setup_env.deploy_graphdb(GRAPHDB_OPTIONS)
        utilprocs.log("Checking if agent registered at BRO")
        wait_for_agent()
        global session
        global driver
        driver = graphdb_util.connectDB(CHART_NAME, NAMESPACE)
        session  = driver.session()
    except Exception:
        # We need to clean up here as teardown is not automatically called
        # if setup fails.
        teardown()
        raise


def teardown():
    utilprocs.log('Removing all helm releases in namespace')
    helm3procs.helm_cleanup_namespace(NAMESPACE)


def test_backup():
    graphdb_util.verifyClusterFormed(NUMBER_OF_CORE + 1, CLUSTER_TIMEOUT_LENGTH, session)
    session.close()
    write_data()

    utilprocs.log(f'Creating backup: {BACKUP_NAME}, scope: {SCOPE}')
    action = BRO.create(BACKUP_NAME, SCOPE)
    wait_for_action(action)
    assert action.result == 'SUCCESS'
    utilprocs.log("Backup completed")


def test_restore():
    utilprocs.log("Deleting Graphdb")
    helm3procs.helm_delete_release(GRAPHDB_RELEASE, NAMESPACE)
    client = k8sclient.KubernetesClient()
    client.wait_for_all_pods_to_terminate(
        NAMESPACE,
        exclude_pods_list=['eric-ctrl-bro-0', client._test_pod_prefix])
    utilprocs.log("Deleted Graphdb")

    # Deploy GraphDb in restore mode
    utilprocs.log("Deploying GraphDB in restore mode")
    restore_options = {"brAgent.restore.state": "ongoing"}
    restore_options.update(GRAPHDB_OPTIONS)
    setup_env.deploy_graphdb(restore_options, wait=False)
    utilprocs.log("Deployed GraphDB in restore mode")
    wait_for_agent()

    utilprocs.log(f'Restoring backup: {BACKUP_NAME}, scope: {SCOPE}')
    action = BRO.restore(BACKUP_NAME, SCOPE)
    wait_for_action(action)
    assert action.result == 'SUCCESS'
    utilprocs.log("Restoring backup data completed")

    helm3procs.helm_wait_for_deployed_release_to_appear(
        GRAPHDB_RELEASE, NAMESPACE, counter=400)
    wait_for_agent()
    utilprocs.log("Restore of GraphDB completed")

    # Validate restore data
    driver = graphdb_util.connectDB(CHART_NAME, NAMESPACE)
    session  = driver.session()
    graphdb_util.verifyClusterFormed(NUMBER_OF_CORE + 1, CLUSTER_TIMEOUT_LENGTH, session)
    
    utilprocs.log('------------------------------------------------')
    utilprocs.log('Connect to the db and get the driver')
    result = list(driver.session().run("MATCH (a:Person) RETURN a"))
    utilprocs.log(result)
    assert len(result) == 1


def wait_for_action(action):
    """Wait for action to complete.
    """
    utilprocs.log(f'{action.name} action started (id: {action.id})')
    timeout = time.time() + ACTION_TIMEOUT
    while action.state == 'RUNNING':
        utilprocs.log(f'{action.name} {action.state}: {action.progress:.0%}')
        assert time.time() < timeout
        time.sleep(5)
    utilprocs.log(f'{action.name} {action.state}: {action.progress:.0%}')
    utilprocs.log(
        f'Result: {action.result}. Result info: {action.result_info}')


def wait_for_agent():
    timeout = time.time() + AGENT_TIMEOUT
    while AGENT_ID not in BRO.status.agents:
        utilprocs.log("Waiting for brAgent to register with BRO...")
        assert time.time() < timeout
        time.sleep(10)
    utilprocs.log("Agent registered, proceeding with next step...")


def write_data():
    utilprocs.log('------------------------------------------------')
    utilprocs.log('Connect to the db and get the driver')
    driver.session().run("CREATE (a:Person {name:'Ruskin Bond', born:1934})")
    session.close()
    utilprocs.log('Test Data written....')
