import redis
from seneca.engine.cr_commands import *
import functools
# TODO -- clean this file up


class RedisProxy:

    def __init__(self, working_db: redis.StrictRedis, master_db: redis.StrictRedis, sbb_idx: int, contract_idx: int,
                 finalize=False):
        self.finalize = finalize
        # TODO do all these fellas need to be passed in? Can we just grab it from the Bookkeeper? --davis
        self.working_db, self.master_db = working_db, master_db
        self.sbb_idx, self.contract_idx = sbb_idx, contract_idx

    def __getattr__(self, item):
        assert item in CRCommandBase.registry, "redis operation {} not implemented for conflict resolution".format(item)

        return CRCommandBase.registry[item](working_db=self.working_db, master_db=self.master_db,
                                            sbb_idx=self.sbb_idx, contract_idx=self.contract_idx,
                                            finalize=self.finalize)
