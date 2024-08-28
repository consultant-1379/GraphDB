#!/usr/bin/python3
import os
import sys
import time
from argparse import ArgumentParser
from logging import FileHandler

from neo4jlib.admin import InitialPasswordAlreadySet
from neo4jlib.client.auth.credentials import credentials
from neo4jlib.client.instance import Neo4jStartupException
from neo4jlib.client.session import Neo4jSession
from neo4jlib.errors import Neo4jNotRunning
from pyu.decor.misc import retry_if_fail
from pyu.error import log_internal_error
from pyu.infra.clustered.consul.errors import ConsulException
from pyu.log import log
from pyu.parallel.defer import defer
from pyu.tools.constants import KILLED_EXIT_CODE
from pyu.tools.locker import named_lock, AlreadyLockedByAnotherPid
from pyu.ui.egress import ExitCodesBase
from logging.handlers import RotatingFileHandler
from lib.dps.threshold import DpsFsThresholdAlreadySetFlag
from lib.conf.template import Neo4jConfTemplate
from pyu.os.fs.units import Size

NEO4J_LOG = '/data/logs/neo4j.log'


class ExitCode(ExitCodesBase):
    successful = 0
    already_running = 0
    failed = 1
    internal_error = 9


def tail_log(shell, log_file):
    while not shell.os.fs.exists(log_file):
        time.sleep(0.2)
        continue
    for line in shell.run('tail -n 0 -f %s' % log_file, defer=True)[1]:
        print(line)


def keep_alive():
    os.system('tail -f /dev/null')  # to keep the container alive forever
    # neo4j = shell.os.sg.neo4j
    # log.verbose = False
    # while neo4j.service.is_running() or not neo4j.hc.is_enabled():
    #     time.sleep(30)


@named_lock('entrypoint')
def entrypoint(shell, args):
    shell.os.fs.make_dirs('/data/logs')
    shell.os.fs.make_dirs('/data/metrics')
    file_size = int(Size('20M').bytes)
    log_handler = RotatingFileHandler('/data/logs/entrypoint.log',
                                      maxBytes=file_size,
                                      backupCount=50)
    log.setup_log(log_handler,
                  'Neo4j entrypoint', verbose=True)
    log.info('##### Entrypoint started at: %s #####' % shell.os.date, True)

    # we want to make sure that for every upgrade, we reset the DPS
    # filesystem threshold value, so we need to remove the flag
    dps_fs_threshold_already_set_flag = DpsFsThresholdAlreadySetFlag(shell)
    defer(dps_fs_threshold_already_set_flag.unset)  # run in the background

    neo4j_sg = shell.os.sg.neo4j
    process = neo4j_sg.service.process
    if process:
        log.info('Neo4j is already running on pid %s' % process.pid, True)
        return ExitCode.already_running

    consts = neo4j_sg.consts
    files = neo4j_sg.files

    plugins_dir = shell.os.fs.get('/plugins')
    if plugins_dir:
        log.info("Copy Neo4j plugins", True)
        plugins_dir.copy_contents_to(consts.plugins_dir)

    log.info("Create Neo4j logs volume symbolic link", True)
    logs_dir = shell.os.fs.get(consts.logs_dir)
    if logs_dir:
        logs_dir.remove(recursive=True)

    logs_mount_dir = shell.os.fs.get('/data/logs')
    logs_mount_dir.create_link(consts.logs_dir, "sTf")

    log.info("Generate extra neo4j config parameters", True)
    template = Neo4jConfTemplate(shell)
    template.generate_neo4j_conf()

    if files.dps_db_dir and files.dps_tx_dir:
        log.info("Run Neo4j Version Uplift, if needed...", True)
        uplift_cmd = "/opt/ericsson/neo4j/uplift/setup.py --verbose"
        status, output = shell.run(uplift_cmd,
                                   env={'PYU_DYNAMIC_OUTPUT': 'false'},
                                   defer=True)
        for line in output:
            log.info(line.encode('ascii', 'ignore').decode('utf-8'), True)
        if status != 0:
            log.error('Neo4j uplift failed with status %s!' % status,
                      True)
            return ExitCode.failed
        log.info("Neo4j Version Uplift finished successfully!", True)
    else:
        shell.os.fs.make_dirs('/data/.uplift/')
        shell.rune('echo 4.4 > /data/.uplift/.already_migrated.flag')
        log.info("Neo4j Initial Install!", True)

    auth_already_set = False
    password = None
    dbms_dir = shell.os.sg.neo4j.files.dbms_dir
    if dbms_dir:
        log.info('dbms/auth.ini is already set', True)
        auth_already_set = True
    else:
        password = retry_if_fail(10, 30, exception=ConsulException) \
            (lambda: credentials(shell).admin.password)()

    log.info("Starting Neo4j service...", True)
    start_cmd = "/ericsson/3pp/neo4j/bin/neo4j start"
    status, output = shell.run(start_cmd,
                               sh_source_path='/etc/neo4j/neo4j_env',
                               defer=True)
    defer(tail_log, shell, NEO4J_LOG)  # run in the background
    start_output_lines = []
    for line in output:
        log.info("%s: %s" % (start_cmd, line), True)
        start_output_lines.append(line)

    if status != 0:
        last_start_output = ' '.join(start_output_lines[:2])
        if 'Neo4j is already running' in last_start_output:
            log.warning('Neo4j is already running!', True)
        else:
            log.error('Neo4j failed to start!', True)
            return ExitCode.failed

    if not auth_already_set:
        try:
            output = shell.admin.set_initial_password(password)
        except InitialPasswordAlreadySet as err:
            log.warning(str(err), True)
        else:
            log.info(output, True)
    instance = shell.instance
    try:
        instance.wait_until_neo4j_is_available(credential=credentials.admin)
    except (Neo4jNotRunning, Neo4jStartupException) as err:
        log.error(str(err), True)
        if not args.leave and not shell.os.sg.neo4j.hc.is_enabled():
            log.info('Neo4j health check is disabled! '
                     'The container will keep running...', True)
            keep_alive()
        raise
    log.info("Neo4j started successfully", True)

    if args.leave:
        return ExitCode.successful
    keep_alive()


def get_args():
    parser = ArgumentParser()
    parser.add_argument('-l', '--leave', dest='leave',
                        action='store_true', help='Start and leave')
    return parser.parse_args()


def main():
    args = get_args()
    with Neo4jSession() as shell:
        try:
            exit_code = entrypoint(shell, args)
        except AlreadyLockedByAnotherPid as err:
            log.warning(str(err), True)
            exit_code = ExitCode.successful
        except BaseException as err:
            if isinstance(err, SystemExit) and err.code == KILLED_EXIT_CODE:
                log.warning('Got SIGTERM: terminated!', True)
                exit_code = err.code
            else:
                exit_code = ExitCode.internal_error
                log_internal_error(stdout=True, stdout_traceback=True)
        log.info('entrypoint.py exiting!', True)

        if exit_code and not args.leave and \
                not shell.os.sg.neo4j.hc.is_enabled():
            log.info('Neo4j health check is disabled! '
                     'CONTAINER KEPT ALIVE FOR TROUBLESHOOTING!', True)
            keep_alive()
        # this is to handle Log-shipper termination
        pid_file = '/logs/app.pid'
        if os.path.exists(pid_file):
            os.remove(pid_file)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
