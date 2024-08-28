#!/usr/bin/python3
import sys
from logging import FileHandler
from logging.handlers import RotatingFileHandler

from lib.probe.base import Probes
from lib.probe.checker import ProbesChecker
from lib.probe.egress import ExitCode
from lib.probe.history import FailureHistoryStorage
from lib.probe.probes import ServiceProbe, Neo4jPingProbe
from lib.probe.tolerance import HealthCheckToleranceStorage
from neo4jlib.client.session import Neo4jSession
from pyu.error import log_internal_error
from pyu.log import log
from pyu.tools.locker import named_lock, AlreadyLockedByAnotherPid
from pyu.os.fs.units import Size

HC_TOLERANCE_FILE = '/data/hc/is_started_tolerance.json'
FAILURES_HISTORY_FILE = '/data/hc/is_started_history.json'
PROBES = Probes(
    "Startup Check",
    ServiceProbe(0),
    Neo4jPingProbe(0),
    max_time=45  # in startupProbe is set to 50.
)


@named_lock('is_started')
def is_started():
    with Neo4jSession() as shell:
        if not shell.os.sg.neo4j.hc.is_enabled():
            log.warning('Neo4j health check is disabled! '
                        'Returning always successful!', True)
            return ExitCode.healthcheck_disabled
        tolerance_storage = HealthCheckToleranceStorage(HC_TOLERANCE_FILE)
        history_storage = FailureHistoryStorage(FAILURES_HISTORY_FILE)
        probes = ProbesChecker(shell, tolerance_storage, history_storage,
                               PROBES, stdout=True,
                               failed_msg='STARTUP NOT COMPLETED YET')
        return probes.check_all()


if __name__ == '__main__':
    try:
        file_size = int(Size('20M').bytes)
        log_handler = RotatingFileHandler('/data/logs/is_started.log',
                                          maxBytes=file_size,
                                          backupCount=50)
        log.setup_log(log_handler, 'is_started')
        exit_code = is_started()
    except AlreadyLockedByAnotherPid as err:
        log.warning(str(err), True)
        exit_code = ExitCode.successful
    except BaseException:
        exit_code = ExitCode.internal_error
        log_internal_error(stdout=True, stdout_traceback=True)
    sys.exit(exit_code)
