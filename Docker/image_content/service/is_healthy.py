#!/usr/bin/python3
import sys
from logging import FileHandler
from logging.handlers import RotatingFileHandler

from lib.probe.base import Probes
from lib.probe.history import FailureHistoryStorage
from lib.probe.tolerance import HealthCheckToleranceStorage
from lib.probe.checker import ProbesChecker
from lib.probe.egress import ExitCode
from lib.probe.probes import ServiceProbe, PortsListeningProbe, \
    Neo4jPingProbe, RoutingTableProbe, CpuThresholdProbe
from lib.dps.threshold import update_dps_filesystem_threshold

from pyu.error import log_internal_error
from pyu.log import log
from pyu.parallel.defer import defer
from pyu.tools.locker import named_lock, AlreadyLockedByAnotherPid
from pyu.tools.timing import MINUTE

from neo4jlib.client.session import Neo4jSession
from pyu.os.fs.units import Size

HC_TOLERANCE_FILE = '/data/hc/is_healthy_tolerance.json'
FAILURES_HISTORY_FILE = '/data/hc/is_healthy_history.json'

PROBES = Probes(
    "Health Check",
    ServiceProbe(0, timeout=10),
    PortsListeningProbe(30, timeout=10),
    Neo4jPingProbe(60, timeout=3 * MINUTE),
    RoutingTableProbe(60, timeout=20),
    CpuThresholdProbe(120, timeout=5),
    max_time=3 * MINUTE + 50  # 230 seconds. In livenessProbe is set to 240.
)
TENTH_OLDEST_TX_TIMESTAMP_PATH_KEY = 'enm/deployment/databases/neo4j/' \
                                     'tenth_oldest_leader_tx_timestamp'


def store_tenth_oldest_tx_timestamp(shell):
    """ THIS IS AN INTERIM WORKAROUND SOLUTION, UNTIL WE GET NEO4J BUG FIXED:
    https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/TORF-555333
    Make sure that we store the the tenth transaction file timestamp into
    consul KV store so the Read-Replica instance can read this value in order
    to determine if a big lag happened.
    From the RR instance, the neo4j-start.sh script, will check:
      - if the latest RR tx file timestamp is older than the tenth oldest
        leader TX file timestamp, then we have a big lag.
    """
    if not shell.instance.is_leader():
        return
    timestamp = ''
    tx_files = sorted(shell.deployment.transaction_files,
                      key=lambda f: f.modified)
    tx_files_length = len(tx_files)
    if tx_files_length > 1:
        # We only store the timestamp when there is more than 1 tx file, to be
        # able to have a fair timestamp comparison on the RR instance. We don't
        # want to compare when we have just 1 tx file for both Leader and RR as
        # the tx file in the RR will obviously be older than the Leader.
        tenth_index = int(tx_files_length * 0.1)  # 10% of the length
        tenth_oldest_tx_file = tx_files[tenth_index]
        timestamp = tenth_oldest_tx_file.modified.isoformat(' ')
    consul = shell.os.clustered.consul
    consul.kv.put(TENTH_OLDEST_TX_TIMESTAMP_PATH_KEY, timestamp)


@named_lock('is_healthy')
def is_healthy():
    with Neo4jSession() as shell:
        if not shell.os.sg.neo4j.hc.is_enabled():
            log.warning('Neo4j health check is disabled! '
                        'Returning always successful!', True)
            return ExitCode.healthcheck_disabled

        # as the below function is an interim solution, we don't want to
        # compromise the actual HC execution time or in case there is an
        # unknown failure, and for this reason we run it in the background
        # using defer():
        defer(store_tenth_oldest_tx_timestamp, shell)

        # the below function update_dps_filesystem_threshold is going to be
        # actually performed only once, as a file flag is created once the
        # threshold value is successfully set via PIB parameter and then the
        # same flag is going to be checked in subsequent executions, so then
        # the function can just ignore the future updates
        defer(update_dps_filesystem_threshold, shell)  # run in the background

        storage = HealthCheckToleranceStorage(HC_TOLERANCE_FILE)
        history = FailureHistoryStorage(FAILURES_HISTORY_FILE)
        probes = ProbesChecker(shell, storage, history, PROBES, stdout=True)
        return probes.check_all()


if __name__ == '__main__':
    try:
        file_size = int(Size('20M').bytes)
        log_handler = RotatingFileHandler('/data/logs/healthcheck.log',
                                          maxBytes=file_size, backupCount=50)
        log.setup_log(log_handler,
                      'is_healthy')
        exit_code = is_healthy()
    except AlreadyLockedByAnotherPid as err:
        log.warning(str(err), True)
        exit_code = ExitCode.successful
    except BaseException:
        exit_code = ExitCode.internal_error
        log_internal_error(stdout=True, stdout_traceback=True)
    sys.exit(exit_code)
