from six import with_metaclass

from lib.probe.tolerance import Tolerance

from pyu.decor.misc import set_timeout, FunctionTimeout
from pyu.log import log
from pyu.tools.timing import JsonableDatetime


class Probes:

    def __init__(self, name, *probes, max_time=None):
        self.name = name
        self._probes = probes
        self.max_time = max_time

    def __call__(self, shell, tolerance_storage, history, stdout=False):
        self._probes = [p(shell, tolerance_storage, history, stdout)
                        for p in self._probes]
        return self

    def __getitem__(self, index):
        return self._probes[index]

    def __iter__(self):
        return iter(self._probes)

    def __len__(self):
        return len(self._probes)

    def __bool__(self):
        return bool(self._probes)


class ProbeFailed(Exception):

    def __init__(self, msg, exit_code):
        super(ProbeFailed, self).__init__(msg)
        self.exit_code = exit_code


class ProbeMeta(type):

    def __new__(mcs, name, bases, attrs):
        """ Automatically decorates every is_ok() method with
        @increment_tolerance_count.
        """

        def increment_tolerance_count(method):
            def wrap(obj):
                ret = method(obj)
                if not ret:
                    obj.tolerance.increment()
                    now = JsonableDatetime.now().isoformat().split('.')[0]
                    obj.history.failures.append("%s %s" % (now, obj.name))
                    obj.history.save()
                    return ret
                obj.tolerance.reset()
                return ret
            return wrap

        attrs['is_ok'] = increment_tolerance_count(attrs['is_ok'])
        return type.__new__(mcs, name, bases, attrs)


class ProbeBase(with_metaclass(ProbeMeta, object)):
    name = None
    failure_exit_code = None
    successful_msg = None
    failure_msg = None

    def __init__(self, max_tolerance, timeout=None):
        self.max_tolerance = max_tolerance
        self.timeout = timeout
        self.shell = None
        self.stdout = None
        self.tolerance = None
        self.history = None

        def check_with_timeout(func):
            def wrapper():
                if not self.timeout:
                    return func()
                try:
                    is_ok = set_timeout(self.timeout)(func)()
                except FunctionTimeout as err:
                    log.warning('Timed out while checking the checkpoint '
                                'ongoing method: %s' % err,
                                stdout=self.stdout)
                    return False
                else:
                    return is_ok
            return wrapper

        # dynamically decorate the is_ok method to check for timeout
        self.is_ok = check_with_timeout(self.is_ok)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Probe: %s>" % self.name

    def __call__(self, shell, tolerance_storage, history, stdout=False):
        k = self.__class__
        assert k.name is not None, "name must be set"
        assert k.failure_exit_code is not None, "failure_exit_code must be set"
        assert k.successful_msg is not None, "successful_msg must be set"
        assert k.failure_msg is not None, "failure_msg must be set"
        self.shell = shell
        self.stdout = stdout
        self.tolerance = Tolerance(tolerance_storage, self)
        self.history = history
        return self

    @property
    def complete_successful_msg(self):
        return self.successful_msg

    @property
    def complete_failure_msg(self):
        msg = self.__class__.failure_msg
        return "%s Failure tolerance: %s/%s." % (msg, self.tolerance.count,
                                                 self.tolerance.max)

    def is_ok(self):
        raise NotImplementedError
