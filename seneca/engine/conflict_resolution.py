import redis
import functools
from seneca.engine.datatypes_base import RObjectMeta
# TODO -- clean this file up

ALL_OPERATIONS = RObjectMeta.all_reads.union(RObjectMeta.all_writes)


class RedisProxy:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 finalize=False):
        self.finalize = finalize
        # TODO: Again, do we need to bind these? Looks like only CRDataStore might need them
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

        self.ds = CRDataStore(working_db=self.working_db, master_db=self.master_db, sbb_idx=self.sbb_idx,
                              contract_idx=self.contract_idx)

    def __getattr__(self, item):
        # If item is a read, read from master layer if we are not finalizing. Otherwise, read from common layer
        if item in RObjectMeta.all_reads:
            if not self.finalize:
                return functools.partial(self.ds.get_master, operation=item)
            else:
                return functools.partial(self.ds.get_common, operation=item)

        # Otherwise, the item is a write operation. If we are not in 'finalize' mode, we should write to our own
        # sub-block-specific namespace. Otherwise, if we are in 'finalize' mode, we write to the common layer
        elif item in RObjectMeta.all_writes:
            if not self.finalize:
                return functools.partial(self.ds.set_working, operation=item)
            else:
                return functools.partial(self.ds.set_common, operation=item)

        else:
            raise Exception("Redis operation '{}' not specified as either a read or write op! Did you "\
                            "define it in an RObject subclasses' _READ_METHODS or _WRITE_METHODS?".format(item))


class CRDataStore:
    """
    ConflictResolutionDataStore

    This class is responsible for interacting with Redis to read and write conflict resolution data
    """

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int=0, contract_idx: int=0):
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

        self._sbb_prefix = "sbb_{}:".format(sbb_idx)
        self._common_prefix = "common:"
        self._mods_key = self._sbb_prefix + 'ordered_mods'  # Key for a list of ordered modifications
        self._status_key = self._sbb_prefix + 'status'  # Key for a list of tx statuses

    def _sbb_prefix_for_key(self, key: str):
        return self._sbb_prefix + key

    def _common_prefix_for_key(self, key: str):
        return self._common_prefix + key

    def get_common(self, key, *args, operation=None, **kwargs):
        common_key = self._common_prefix_for_key(key)

        # First check if the key exists in the common layer on working_db, and return it if so
        if self.working_db.exists(common_key):
            return getattr(self.working_db, operation)(common_key, *args, **kwargs)

        # Otherwise, get the key from the master layer
        else:
            assert self.master_db.exists(key), "Key {} not found in common layer or Master DB!".format(key)
            return getattr(self.master_db, operation)(key, *args, **kwargs)

    def set_common(self, key, *args, operation=None, **kwargs):
        common_key = self._common_prefix_for_key(key)
        return getattr(self.working_db, operation)(common_key, *args, **kwargs)

    def get_master(self, key, *args, operation=None, **kwargs):
        return getattr(self.master_db, operation)(key, *args, **kwargs)

    def set_master(self, key, *args, operation=None, **kwargs):
        return getattr(self.master_db, operation)(key, *args, **kwargs)

    def set_working(self, key, *args, operation=None, **kwargs):
        working_key = self._sbb_prefix_for_key(key)
        return getattr(self.working_db, operation)(working_key, *args, **kwargs)
        # TODO add this to list of modifications

    def get_working(self, key, *args, operation=None, **kwargs):
        working_key = self._sbb_prefix_for_key(key)
        return getattr(self.working_db, operation)(working_key, *args, **kwargs)


