#!/usr/bin/python3
import sys

from neo4jlib.client.auth.credentials import credentials
from neo4jlib.client.instance import Neo4jStartupTimeout, Neo4jStartupError
from neo4jlib.client.session import Neo4jSession
from neo4jlib.env.healthcheck import Neo4jHealthCheckDisabledBlock
from neo4jlib.rescue.recover import Neo4jClusterRecoveryVenm
from pyu.error import log_internal_error
from pyu.tools.timing import MINUTE
from pyu.log import log


def return_neo4j_operational():
    """ Checks if Neo4j is up and restores it if it's not
    :return: None
    """
    with Neo4jSession() as shell:
        with Neo4jHealthCheckDisabledBlock(shell):
            service = shell.os.sg.neo4j.service
            if not service.is_running():
                log.info('Starting Neo4j as part of backup cleanup',
                         stdout=True)
                service.start()
            try:
                # wait until Neo4j is running
                shell.instance.wait_until_neo4j_is_available(
                    credential=credentials.admin, timeout=30 * MINUTE)
            except (Neo4jStartupError, Neo4jStartupTimeout) as exc:
                log.warning('Failed to wait for Neo4j to start: %s. An '
                            'automated recovery attempt to allow story copy '
                            'will start now.'
                            % exc, stdout=True)
                # try to recover
                recovery = Neo4jClusterRecoveryVenm(verbose=True)
                recovery.allow_store_copy(shell)
            else:
                log.info('Neo4j started successfully!', stdout=True)


if __name__ == "__main__":
    log.setup_syslog("backup_cleanup.py", True)
    try:
        sys.exit(return_neo4j_operational())
    except Exception as err:
        log_internal_error(stdout_traceback=True)
        sys.exit(1)
