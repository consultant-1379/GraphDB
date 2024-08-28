#!/usr/bin/python3

import sys
import time
from logging import FileHandler
from logging.handlers import RotatingFileHandler

from pyu.error import Timeout

from neo4jlib.client.cluster.constants import LAG_THRESHOLD
from neo4jlib.client.session import Neo4jSession
from pyu.error import log_internal_error
from pyu.infra.clustered.consul.errors import ConsulException
from pyu.log import log
from pyu.parallel.threads import ThreadPool
from pyu.tools.text import comma
from pyu.tools.timing import TimeWindow, HOUR, MINUTE
from pyu.os.fs.units import Size


def wait_until_followers_are_not_lagged(instance):
    log.debug('wait_until_followers_are_not_lagged for %s' % instance, True)
    with TimeWindow() as t:
        had_lag = False
        lag = None
        max_lag = lag
        while lag is None or lag >= LAG_THRESHOLD:
            with TimeWindow() as none_lag_tw:
                while lag is None:
                    try:
                        lag = instance.lag
                    except Exception as exc:
                        log.error('Unable to determine lag: %s' % exc, True)
                        return
                    if lag is None:
                        time.sleep(10)
                        if none_lag_tw.elapsed > MINUTE:
                            log.warning('Unable to determine lag for longer '
                                        'than minute as the value comes None',
                                        True)
                            return
            if not max_lag or lag > max_lag:
                max_lag = lag
            log.info('Lag of %s is %s' % (instance, lag), True)
            if t.elapsed > HOUR:
                raise Timeout('Wait for lag to reduce below %s between %s and '
                              'the leader timed out after 1 hour' %
                              (LAG_THRESHOLD, instance.host.alias))
            if lag < LAG_THRESHOLD:
                break
            had_lag = True
            time.sleep(60)

        if had_lag:
            log.warning('There was a lag %s greater than the threshold %s '
                        'between %s and the leader but it reduced down in '
                        '%s' % (max_lag, LAG_THRESHOLD, instance.host.alias,
                                t.elapsed_display), True)
        else:
            log.info('There was no considerable lag %s between %s and the '
                     'leader' % (max_lag, instance.host.alias), True)


def main():
    with Neo4jSession() as shell:
        try:
            pool = ThreadPool()
            try:
                followers = shell.cluster.followers
            except ConsulException as exc:
                log.error('Failed to obtain Neo4j followers: %s' % exc, True)
            else:
                for instance in followers:
                    pool.add_named(wait_until_followers_are_not_lagged,
                                   str(instance.host), instance)
                log.info('Waiting IN PARALLEL for potential lag between the '
                         'leader and the followers %s.' %
                         comma(map(str, [f.host for f in followers])), True)
                pool.start()
                pool.wait()
        except Timeout as err:
            log.error(str(err), True)
            return 2
        except Exception:
            log_internal_error(stdout_traceback=True)
            return 1
        finally:
            # we need to make sure that Neo4j is gracefully stopped anyway
            log.info('Stopping neo4j...', True)
            shell.os.sg.neo4j.service.stop()
            log.info('Neo4j successfully stopped!', True)


if __name__ == '__main__':
    file_size = int(Size('20M').bytes)
    log_handler = RotatingFileHandler('/data/logs/stop.log',
                                      maxBytes=file_size,
                                      backupCount=50)
    log.setup_log(log_handler, 'stop', verbose=True)
    try:
        exit_code = main()
    except Exception:
        log_internal_error(stdout_traceback=True)
        exit_code = 1
    sys.exit(exit_code)
