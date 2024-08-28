
from pyu.tools.stash import KvStashBase, Key


class Tolerance(object):

    def __init__(self, storage, probe):
        self.storage = storage
        self.probe = probe

    def __str__(self):
        return "%s/%s" % (self.count, self.max)

    def __repr__(self):
        return "<Tolerance for %s: %s>" % (self.probe.name, self)

    @property
    def count(self):
        return getattr(self.storage, self._count_attr_name)

    @property
    def max(self):
        return self.probe.max_tolerance

    def reached(self):
        return self.count > self.max

    def increment(self):
        setattr(self.storage, self._count_attr_name, self.count + 1)

    def reset(self):
        setattr(self.storage, self._count_attr_name, 0)

    @property
    def _count_attr_name(self):
        return 'failed_%s_count' % self.probe.name


class HealthCheckToleranceStorage(KvStashBase):
    """ Stores the maximum number of failures tolerated and the number of
    failures. All values are going to be saved in the file HC_TOLERANCE_FILE.
    """
    failed_service_count = Key(int, default=0)
    failed_listening_count = Key(int, default=0)
    failed_ping_count = Key(int, default=0)
    failed_routing_count = Key(int, default=0)
