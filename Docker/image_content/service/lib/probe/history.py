from pyu.tools.stash import KvStashBase, Key


class FailureHistoryStorage(KvStashBase):

    failures = Key(list, default=[])
