from pyu.log import log
from pyu.enm.pib import PibConfig
from pyu.os.apis.curl import ResponseFailed
from pyu.os.fs.units import Size


class DpsFsThresholdAlreadySetFlag(object):
    """ It represents the flag that will tell whether the DPS filesystem
    threshold value has been set or not.
    """

    file_path = '/data/.dps_fs_threshold.flag'

    def __init__(self, shell):
        self.shell = shell

    def __str__(self):
        return self.file_path

    @property
    def file(self):
        return self.shell.os.fs.get(self.file_path)

    def set(self):
        self.shell.os.fs.touch(self.file_path)

    def unset(self):
        file_flag = self.file
        if file_flag:
            file_flag.remove()

    def __bool__(self):
        """ If the file exists, it means that the DPS filesystem threshold
        value is already set.
        """
        return bool(self.file)

    def __nonzero__(self):  # python 2
        return self.__bool__()


def update_dps_filesystem_threshold(shell, force=False):
    """ Updates the DPS filesystem threshold value.
    We need to make sure that this function is not fully executed everytime, so
    we keep the flag DpsFsThresholdAlreadySetFlag set as a cache.
    If force=True, then the flag is ignored.
    """
    already_set_flag = DpsFsThresholdAlreadySetFlag(shell)
    if not force and already_set_flag:
        log.debug('Flag %s found, DPS filesystem threshold is already set' %
                  already_set_flag, True)
        return
    parameter = 'databaseSpaceCriticalThreshold'
    pib_host = shell.os.env.pib_connection_host
    pib = PibConfig(shell, pib_host.given_host)
    try:
        value = pib.read(parameter)
    except ResponseFailed as err:
        log.error('Failed response while trying to get %s value: %s' %
                  (parameter, err), True)
        value = ''
    dps_fs_threshold = shell.dps.fs_threshold
    if value.strip():
        threshold = Size('%sm' % value)
        if dps_fs_threshold == threshold:
            log.info('PIB parameter %s is already set to %sm=%s' %
                     (parameter, value, threshold), True)
            already_set_flag.set()
            return
        log.warning('PIB parameter %s is currently set to %sm~%s, however '
                    'the advised value must be %sm=%s' %
                    (parameter, value, threshold, dps_fs_threshold.megas,
                     dps_fs_threshold), True)
    else:
        log.warning('PIB parameter %s not set yet' % parameter, True)
    log.info('Updating %s value to %sm=%s' %
             (parameter, dps_fs_threshold.megas, dps_fs_threshold), True)
    try:
        pib.update(parameter, dps_fs_threshold.megas)
    except ResponseFailed as err:
        log.error('Failed response while trying to update %s value to '
                  '%sm=%s: %s' % (parameter, dps_fs_threshold.megas,
                                  dps_fs_threshold, err), True)
    else:
        log.info('PIB parameter %s has been successfully updated to %sm=%s' %
                 (parameter, dps_fs_threshold.megas, dps_fs_threshold), True)
        already_set_flag.set()


if __name__ == '__main__':
    # this module can be executed as a solo script
    from neo4jlib.client.session import Neo4jSession
    with Neo4jSession() as shell:
        update_dps_filesystem_threshold(shell, force=True)
