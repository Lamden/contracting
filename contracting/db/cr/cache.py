# Builtin imports

# Local imports
from contracting.logger import get_logger
from contracting.db.driver import ContractDriver, CacheDriver
from contracting import config
from contracting.db.cr.callback_data import ExecutionData, SBData
from typing import List

import json

# TODO include _key exclusions for stamps, etc
class Macros:
    # TODO we need to make sure these keys dont conflict with user stuff in the common layer. I.e. users cannot be
    # creating keys with the same names
    CONFLICT_RESOLUTION = '_conflict_resolution_phase'
    RESET = "_reset_phase"

    ALL_MACROS = [CONFLICT_RESOLUTION, RESET]

class CRCache:

    def __init__(self, idx, master_db, sbb_idx, num_sbb, executor):
        self.idx = idx
        self.sbb_idx = sbb_idx
        self.num_sbb = num_sbb
        self.executor = executor

        self.bag = None            # Bag will be set by the execute call
        self.rerun_idx = None      # The index to being reruns at
        self.results = {}          # The results of the execution
        self.macros = Macros()     # Instance of the macros class for mutex/sync
        self.input_hash = None     # The 'input hash' of the bag we are executing, a 64 char hex str

        name = self.__class__.__name__ + "[cache-{}]".format(self.idx)
        self.log = get_logger(name)

        # Replace DB with a Cache thing that either gets from itself or the raw db supplied.
        self.db = ContractDriver(db=self.idx)

        # This is the state driver
        self.master_db = master_db

        self._reset_macro_keys()

    def _incr_macro_key(self, macro):
        self.log.spam("INCREMENTING MACRO {}".format(macro))
        self.db.incrby(macro)

    def _get_macro_value(self, macro_key):
        val = self.db.get_direct(macro_key)
        return int(val) if val is not None else -1

    def _reset_macro_keys(self):
        self.log.spam("{} is resetting macro keys".format(self))
        for key in Macros.ALL_MACROS:
            self.db.set_direct(key, 0)

    def get_results(self):
        return self.results

    def execute_bag(self, bag):
        self.log.debugv("{} is executing transactions!".format(self))

        self.bag = bag
        # Execute first round using Master DB Driver since we will not have any keys in common
        # Do not commit, leveraging cache only
        self.results = self.executor.execute_bag(self.bag, environment=self.bag.environment, driver=self.master_db)

        # Copy the cache from Master DB Driver to the contained Driver for common
        self.db.reset_cache(modified_keys=self.master_db.modified_keys,
                            contract_modifications=self.master_db.contract_modifications,
                            original_values=self.master_db.original_values)
        # Reset the master_db cache back to empty
        self.master_db.reset_cache()


    def my_turn_for_cr(self):
        return self._get_macro_value(Macros.CONFLICT_RESOLUTION) == self.sbb_idx

    def prepare_reruns(self):
        # Find all instances where our originally grabbed value from the cache does not
        # match the value in the DB, cascade from common to master, if the _key doesn't
        # exist in common, check master since another CRCache may have merged since you
        # executed.
        cr_key_hits = []
        for key, value in self.db.original_values.items():
            if key not in cr_key_hits:
                common_db_value = self.db.get(key)
                if common_db_value is not None:
                    if common_db_value != value:
                        cr_key_hits.append(key)
                else:
                    master_db_value = self.master_db.get(key)
                    if master_db_value != value:
                        cr_key_hits.append(key)

        # Check the modified keys list for the lowest contract index, set that as the
        # rerun index so we can rerun all contracts following the first mismatch
        if len(cr_key_hits) > 0:
            cr_key_modifications = {k: v for k, v in self.db.modified_keys.items() if k in cr_key_hits}
            self.rerun_idx = 999999
            for key, value in cr_key_modifications.items():
                if value[0] < self.rerun_idx:
                    self.rerun_idx = value[0]

    def requires_reruns(self):
        return self.rerun_idx is not None

    def rerun_transactions(self):
        self.db.revert(idx=self.rerun_idx)
        self.bag.yield_from(idx=self.rerun_idx)
        self.results.update(self.executor.execute_bag(self.bag, environment=self.bag.environment, driver=self.db))

    def resolve_conflicts_and_merge(self):
        self.log.debugv("{} is resolving conflicts!".format(self))
        self.prepare_reruns()
        if self.requires_reruns():
            self.rerun_transactions()

        # call completion handler on bag so Cilantro can build a SubBlockContender
        self.bag.completion_handler(self.bag.sub_block_idx, self._get_sb_data())
        self._incr_macro_key(Macros.CONFLICT_RESOLUTION)

        self.db.commit()  # this will wipe the cache   ?? is this right, raghu todo

    def cr_event(self):
        if self.my_turn_for_cr():
            self.resolve_conflicts_and_merge()

    def all_committed(self):
        return self._get_macro_value(Macros.CONFLICT_RESOLUTION) == self.num_sbb

    def merge_to_master(self):
        assert self.all_committed(), "Calling premature merge to master!"
        if self.sbb_idx == 0:
            merge_keys = [ x for x in self.db.keys() if x not in Macros.ALL_MACROS ]
            for key in merge_keys:
                self.master_db.set(key, self.db.get(key))
            self.master_db.commit()

    def reset_dbs(self):
        # now reset dbs
        self.db.reset_cache()
        self.master_db.reset_cache()
        self.rerun_idx = None
        self.bag = None
        self._incr_macro_key(Macros.RESET)

    def is_reset(self):
        return (self._get_macro_value(Macros.RESET) == 0) if self.sbb_idx != 0 \
               else (self._get_macro_value(Macros.RESET) == self.num_sbb)

    def mark_clean(self):
        # If we are on SBB 0, we need to flush the common layer of this cache
        # since the DB is shared, we only need to call this from one of the SBBs
        # TODO - this should be a macro so we can switch to other sbbers if needed
        if self.sbb_idx == 0:
            self.log.debugv("{} is flushing db!".format(self))
            self.db.flush()
            self._reset_macro_keys()

    def _get_sb_data(self) -> SBData:
        if len(self.results) != len(self.bag.transactions):
            self.log.critical("Mismatch of state: length of results is {} but bag has {} txs. Discarding." \
                              .format(len(self.results), len(self.bag.transactions)))
            self.discard()
            return [] # colin is this necessary?? also what should i return for cilatnro to be aware of the goof?

        tx_datas = []
        i = 0

        # Iterate over results to take into account transactions that have been reverted and removed from contract_mods
        # This is the most evil code written by man
        for tx_idx in sorted(self.results.keys()):

            status_code, result, stamps = self.results[tx_idx]
            state_str = ""

            if status_code == 0:
                mods = self.db.contract_modifications[i]
                i += 1
                state_str = json.dumps(mods)

            tx_datas.append(ExecutionData(contract=self.bag.transactions[tx_idx], status=status_code,
                                          response=result, state=state_str, stamps=stamps))

        return SBData(self.bag.input_hash, tx_data=tx_datas)

    def _get_macro_values(self):
        mv_str = ''
        for key in Macros.ALL_MACROS:
            mv_str += str(self._get_macro_value(key)) + ' '
        return mv_str

    def __repr__(self):
        input_hash = 'NOT_SET' if self.bag is None else self.bag.input_hash
        return "<CRCache input_hash={}, idx={}, sbb_idx={}, macros={}>"\
               .format(input_hash, self.idx, self.sbb_idx, self._get_macro_values())


if __name__ == "__main__":
    c = CRCache(1,1,1,1,1)
