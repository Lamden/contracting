# Builtin imports


# Third party imports
from transitions import Machine
from transitions.extensions.states import add_state_features, Timeout
from transitions.extensions import GraphMachine

# Local imports
from contracting.logger import get_logger
from contracting.db.driver import ContractDriver, CacheDriver
from contracting.db.encoder import decode, encode
from contracting.db.cr.transaction_bag import TransactionBag
from contracting import config

# TODO include key exclusions for stamps, etc
class Macros:
    # TODO we need to make sure these keys dont conflict with user stuff in the common layer. I.e. users cannot be
    # creating keys named '_execution' or '_conflict_resolution'
    EXECUTION = '_execution_phase'
    CONFLICT_RESOLUTION = '_conflict_resolution_phase'
    RESET = "_reset_phase"

    ALL_MACROS = [EXECUTION, CONFLICT_RESOLUTION, RESET]


@add_state_features(Timeout)
class CustomStateMachine(GraphMachine):
    def __init__(self, *args, **kwargs):
        kwargs['show_conditions'] = True
        kwargs['title'] = 'CRCache State Machine'
        super().__init__(*args, **kwargs)

class CRCache:

    states = [
        {'name': 'CLEAN'},
        {'name': 'BAG_SET'},
        {'name': 'EXECUTED', 'timeout': config.EXEC_TIMEOUT, 'on_timeout': 'discard'},
        {'name': 'CR_STARTED'},
        {'name': 'REQUIRES_RERUN'},
        {'name': 'READY_TO_COMMIT'},
        {'name': 'COMMITTED', 'timeout': config.CR_TIMEOUT, 'on_timeout': 'discard'},
        {'name': 'READY_TO_MERGE'},
        {'name': 'MERGED'},
        {'name': 'DISCARDED'},
        {'name': 'RESET'}
    ]

    def __init__(self, idx, master_db, sbb_idx, num_sbb, executor):
        self.idx = idx
        self.sbb_idx = sbb_idx
        self.num_sbb = num_sbb
        self.executor = executor

        self.bag = None            # Bag will be set by the execute call
        self.rerun_idx = None      # The index to being reruns at
        self.results = {}          # The results of the execution
        self.top_of_stack = False  # Whether or not we're top of the stack (told by Client)
        self.macros = Macros()     # Instance of the macros class for mutex/sync

        name = self.__class__.__name__ + "[cache-{}]".format(self.idx)
        self.log = get_logger(name)

        self.db = ContractDriver(db=self.idx)
        self.master_db = master_db

        transitions = [
            {
                'trigger': 'set_bag',
                'source': 'CLEAN',
                'dest': 'BAG_SET',
                'before': 'set_transaction_bag'
            },
            {
                'trigger': 'execute',
                'source': 'BAG_SET',
                'dest': 'EXECUTED',
                'prepare': '_reset_macro_keys',
                'before': 'execute_transactions'
            },
            { # ASYNC CALL TO MOVE OUT FROM EXECUTED sync_execution
                'trigger': 'sync_execution',
                'source': 'EXECUTED',
                'dest': 'CR_STARTED',
                'conditions': ['my_turn_for_cr', 'is_top_of_stack'],
                'after': 'start_cr'
            },
            {
                'trigger': 'start_cr',
                'source': 'CR_STARTED',
                'dest': 'READY_TO_COMMIT',
                'prepare': 'prepare_reruns',
                'unless': 'requires_reruns'
            },
            {
                'trigger': 'start_cr',
                'source': 'CR_STARTED',
                'dest': 'REQUIRES_RERUN',
                'conditions': 'requires_reruns',
                'after': 'rerun'
            },
            {
                'trigger': 'rerun',
                'source': 'REQUIRES_RERUN',
                'dest': 'READY_TO_COMMIT',
                'before': 'rerun_transactions'
            },
            {
                'trigger': 'commit',
                'source': 'READY_TO_COMMIT',
                'dest': 'COMMITTED',
                'before': 'merge_to_common'
            },
            { # ASYNC CALL FROM OUTSIDE, TIMEOUT HERE TO ERROR
                'trigger': 'sync_merge_ready',
                'source': 'COMMITTED',
                'dest': 'READY_TO_MERGE',
                'conditions': 'all_committed',
            },
            { # WILL WAIT HERE FOR MERGE TO BE CALLED
                'trigger': 'merge',
                'source': 'READY_TO_MERGE',
                'dest': 'MERGED',
                'before': 'merge_to_master',
                'after': 'reset'
            },
            {
                'trigger': 'reset',
                'source': ['MERGED', 'DISCARDED'],
                'dest': 'RESET',
                'before': 'reset_dbs'
            },
            {
                'trigger': 'sync_reset',
                'source': 'RESET',
                'dest': 'CLEAN',
                'conditions': 'all_reset'
            },
            {
                'trigger': 'discard',
                'source': ['BAG_SET', 'EXECUTED', 'CR_STARTED', 'REQUIRES_RERUN', 'READY_TO_COMMIT', 'COMMITTED', 'READY_TO_MERGE'],
                'dest': 'DISCARDED',
                'after': 'reset'
            }
        ]
        self.machine = CustomStateMachine(model=self, states=CRCache.states,
                                          transitions=transitions, initial='CLEAN')

    def _incr_macro_key(self, macro):
        self.db.incrby(macro)

    def _check_macro_key(self, macro):
        val = decode(super(CacheDriver, self.db).get(macro))
        print("MACRO: {} VAL: {} VALTYPE: {}".format(macro, val, type(val)))
        return val

    def _reset_macro_keys(self):
        for key in Macros.ALL_MACROS:
            self.db.delete(key)
            super(CacheDriver, self.db).set(key, encode(0))

    def get_results(self):
        return self.results

    def set_transaction_bag(self, bag):
        self.bag = bag

    def execute_transactions(self):
        # Execute first round using Master DB Driver since we will not have any keys in common
        # Do not commit, leveraging cache only
        self.results = self.executor.execute_bag(self.bag, self.master_db)

        # Copy the cache from Master DB Driver to the contained Driver for common
        self.db.reset_cache(modified_keys=self.master_db.modified_keys,
                            contract_modifications=self.master_db.contract_modifications,
                            original_values=self.master_db.original_values)
        # Reset the master_db cache back to empty
        self.master_db.reset_cache()

        # Increment the execution macro
        self._incr_macro_key(Macros.EXECUTION)

    def my_turn_for_cr(self):
        return self._check_macro_key(Macros.CONFLICT_RESOLUTION) == self.sbb_idx

    def set_top_of_stack(self):
        self.top_of_stack = True

    def is_top_of_stack(self):
        return self.top_of_stack

    def prepare_reruns(self):
        # Find all instances where our originally grabbed value from the cache does not
        # match the value in the DB, cascade from common to master, if the key doesn't
        # exist in common, check master since another CRCache may have merged since you
        # executed.
        cr_key_hits = []
        for key, value in self.db.original_values.items():
            if key not in cr_key_hits:
                common_db_value = super(CacheDriver, self.db).get(key)
                if common_db_value is not None:
                    if common_db_value != value:
                        cr_key_hits.append(key)
                else:
                    master_db_value = super(CacheDriver, self.master_db).get(key)
                    if master_db_value != value:
                        cr_key_hits.append(key)

        # Check the modified keys list for the lowest contract index, set that as the
        # rerun index so we can rerun all contracts following the first mismatch
        if len(cr_key_hits) > 0:
            cr_key_modifications = {k: v for k, v in self.db.modified_keys.items() if k in cr_key_hits}
            self.rerun_idx = 999999
            for key, value in cr_key_modifications:
                if value[0] < self.rerun_idx:
                    self.rerun_idx = value[0]

    def requires_reruns(self):
        return self.rerun_idx is not None

    def rerun_transactions(self):
        self.db.revert(idx=self.rerun_idx)
        self.bag.yield_from(idx=self.rerun_idx)
        self.results.update(self.executor.execute_bag(self.bag))

    def merge_to_common(self):
        self.db.commit()
        self._incr_macro_key(Macros.CONFLICT_RESOLUTION)

    def all_committed(self):
        return self._check_macro_key(Macros.CONFLICT_RESOLUTION) == self.num_sbb

    def merge_to_master(self):
        if self.sbb_idx == 0:
            self.master_db.commit()

    def reset_dbs(self):
        # If we are on SBB 0, we need to flush the common layer of this cache
        # since the DB is shared, we only need to call this from one of the SBBs
        if self.sbb_idx == 0:
            self.db.flush()
        self.db.reset_cache()
        self.master_db.reset_cache()
        self.rerun_idx = None
        self._incr_macro_key(Macros.RESET)

    def all_reset(self):
        return self._check_macro_key(Macros.RESET) == self.num_sbb

if __name__ == "__main__":
    c = CRCache(1,1,1,1,1)
    c.machine.get_graph().draw('CRCache_StateMachine.png', prog='dot')