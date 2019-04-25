# Builtin imports


# Third party imports
from transitions import Machine
from transitions.extensions.states import add_state_features, Timeout
from transitions.extensions import GraphMachine

# Local imports
from seneca.logger import get_logger
from seneca.db.driver import DatabaseDriver
from seneca import config


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
        {'name': 'EXECUTED', 'timeout': config.EXEC_TIMEOUT, 'on_timeout': 'error'},
        {'name': 'CR_STARTED'},
        {'name': 'REQUIRES_RERUN'},
        {'name': 'READY_TO_COMMIT'},
        {'name': 'COMMITTED', 'timeout': config.CR_TIMEOUT, 'on_timeout': 'error'},
        {'name': 'READY_TO_MERGE'},
        {'name': 'MERGED'},
        {'name': 'DISCARDED'},
        {'name': 'RESET'},
        {'name': 'ERROR'}
    ]

    def __init__(self, idx, master_db, sbb_idx, num_sbb, executor):
        self.idx = idx
        self.sbb_idx = sbb_idx
        self.num_sbb = num_sbb

        name = self.__class__.__name__ + "[cache-{}]".format(self.idx)
        self.log = get_logger(name)

        self.db = DatabaseDriver(db=self.idx)
        self.master_db = master_db

        transitions = [
            {
                'trigger': 'execute',
                'source': 'CLEAN',
                'dest': 'EXECUTED',
                'before': 'execute_transactions',
            },
            { # ASYNC CALL TO MOVE OUT FROM EXECUTED sync_execution
                'trigger': 'sync_execution',
                'source': 'EXECUTED',
                'dest': 'CR_STARTED',
                'conditions': ['my_turn', 'top_of_stack'],
                'after': 'start_cr'
            },
            {
                'trigger': 'start_cr',
                'source': 'CR_STARTED',
                'dest': 'READY_TO_COMMIT',
                'unless': 'requires_reruns',
                'after': 'commit'
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
                'before': 'rerun_transactions',
                'after': 'commit'
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
                'trigger': 'discard',
                'source': 'ERROR',
                'dest': 'DISCARDED',
                'before': 'discard_commit',
                'after': 'reset'
            },
            {
                'trigger': 'reset',
                'source': ['MERGED', 'DISCARDED'],
                'dest': 'RESET',
                'before': 'reset_caches'
            },
            {
                'trigger': 'clean',
                'source': 'RESET',
                'dest': 'CLEAN',
                'conditions': 'all_reset',
                'before': 'clean_caches'
            },
            {
                'trigger': 'error',
                'source': ['EXECUTED', 'REQUIRES_RERUN', 'READY_TO_COMMIT', 'COMMITTED', 'READY_TO_MERGE', 'MERGED'],
                'dest': 'ERROR',
                'after': 'discard'
            }
        ]
        self.machine = CustomStateMachine(model=self, states=CRCache.states,
                                          transitions=transitions, initial='CLEAN')

        self.executor = executor
        self.macros = Macros()


    def _incr_macro_key(self, macro):
        self.db.incrby(macro)

    def _check_macro_key(self, macro):
        return self.db.get(macro) == self.num_sbb

    def _reset_macro_keys(self):
        for key in Macros.ALL_MACROS:
            self.db.delete(key)

    def execute_transactions(self):
        self.incr_macro_key(Macros.EXECUTION)
        return

    def all_executed(self):
        return self._check_macro_key(Macros.EXECUTION)

    def requires_reruns(self):
        return

    def rerun_transactions(self):
        return

    def merge_to_common(self):
        self.incr_macro_key(Macros.CONFLICT_RESOLUTION)
        return

    def all_committed(self):
        return self._check_macro_key(Macros.CONFLICT_RESOLUTION)

    def merge_to_master(self, ):
        return

    def discard_commit(self):
        return

    def reset_caches(self):
        self.incr_macro_key(Macros.RESET)

    def clean_caches(self):
        self.reset_macro_keys()


if __name__ == "__main__":
    c = CRCache(1,1,1,1,1)
    c.machine.get_graph().draw('CRCache_StateMachine.png', prog='dot')