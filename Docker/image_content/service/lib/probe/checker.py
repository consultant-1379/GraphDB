from lib.probe.egress import ExitCode

from pyu.decor.misc import max_time
from pyu.log import log
from pyu.tools.timing import TimeWindow


class ProbesChecker(object):

    def __init__(self, shell, tolerance_storage, history, probes, **kwargs):
        self.shell = shell
        self.stdout = kwargs.pop('stdout', False)
        self.failed_msg = kwargs.pop('failed_msg', 'PROBE CHECK FAILED')
        self.probes = probes(shell, tolerance_storage, history, self.stdout)
        # decorate check_all dynamically to set a global max_time to prevent
        # the entire execution time to exceed the livenessProbe timeout
        self.check_all = max_time(self.probes.max_time)(self.check_all)

    def check_all(self):

        def finished_msg(message, successful=None):
            if successful is None:
                emoji = ':|'
            else:
                emoji = ':)' if successful else ':('
            return "%s Probe duration: %s. %s %s" % \
                   (probe.name.title(), probe_time.elapsed_display_short,
                    message, emoji)

        name = self.probes.name.upper()
        with TimeWindow() as whole_time:
            for probe in self.probes:
                with TimeWindow() as probe_time:
                    if not probe.is_ok():
                        if probe.tolerance.reached():
                            msg = '%s %s' % (probe.complete_failure_msg,
                                             self.failed_msg)
                            log.error(finished_msg(msg, successful=False),
                                      self.stdout)
                            log.error('%s FAILED! Duration: %s' %
                                      (name, whole_time.elapsed_display_short),
                                      self.stdout)
                            return probe.failure_exit_code
                        msg = '%s Returning successful for now' % \
                              probe.complete_failure_msg
                        log.warning(finished_msg(msg), self.stdout)
                        log.info('%s HALF PASSED. Duration: %s' %
                                 (name, whole_time.elapsed_display_short),
                                 self.stdout)
                        return ExitCode.successful
                    log.info(finished_msg(probe.successful_msg,
                                          successful=True),
                             self.stdout)
            log.info('%s SUCCESSFULLY PASSED. Duration: %s' %
                     (name, whole_time.elapsed_display_short),
                     self.stdout)
        return ExitCode.successful
