from collections import deque
import time, asyncio, ujson as json, redis
from seneca.libs.logger import get_logger
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.constants.config import *
from seneca.engine.conflict_resolution import CRContext
from seneca.engine.book_keeper import BookKeeper
from collections import deque, defaultdict
from typing import Callable, List

SUCC_FLAG = 'SUCC'


class Macros:
    # TODO we need to make sure these keys dont conflict with user stuff in the common layer. I.e. users cannot be
    # creating keys named '_execution' or '_conflict_resolution'
    EXECUTION = '_execution'
    CONFLICT_RESOLUTION = '_conflict_resolution'

    ALL_MACROS = [EXECUTION, CONFLICT_RESOLUTION]


class Phase:
    EXEC_TIMEOUT = 14  # Number of seconds client will wait for other clients to finish execution phase
    CR_TIMEOUT = 14  # Number of seconds client will wait for other clients to finish conflict resolution phase
    BLOCK_TIMEOUT = 30  # Number of seconds a pending db will wait until it is at the top (first element) of pending_dbs
    POLL_INTERVAL = 0.5  # Poll for Phase changes every POLL_INTERVAL seconds

    @staticmethod
    def reset_phase_variables(db):
        db.set(Macros.EXECUTION, 0)
        db.set(Macros.CONFLICT_RESOLUTION, 0)

    @staticmethod
    def incr_phase_variable(db, key):
        db.incr(key)

    @staticmethod
    def get_phase_variable(db, key):
        if not db.exists(key):
            return 0
        return int(db.get(key).decode())


class SenecaClient(SenecaInterface):

    def __init__(self, sbb_idx, num_sbb, concurrent_mode=True, loop=None):
        # TODO do we even need to bother with the concurrent_mode flag? We are treating that its always true --davis
        super().__init__()

        name = self.__class__.__name__ + "[sbb-{}]".format(sbb_idx)
        self.log = get_logger(name)
        self.loop = loop or asyncio.get_event_loop()

        self.port = get_redis_port()
        self.password = get_redis_password()

        self.sbb_idx = sbb_idx
        self.num_sb_builders = num_sbb
        self.concurrent_mode = concurrent_mode
        self.max_number_workers = NUM_CACHES

        self.master_db = None  # A redis.StrictRedis instance
        self.active_db = None  # Set to a CRContext instance
        self.available_dbs = deque()  # List of CRContext instances
        self.pending_dbs = deque()  # List of CRContext instances
        self.pending_futures = {}  # Map of input hashes -> {'fut': asyncio.Future, 'data': CRContext}

        self._setup_dbs()

    def _setup_dbs(self):
        self.master_db = redis.StrictRedis(host='localhost', port=self.port, db=MASTER_DB, password=self.password)
        for db_num in range(self.max_number_workers):
            db_client = redis.StrictRedis(host='localhost', port=self.port, db=db_num+DB_OFFSET, password=self.password)
            cr_data = CRContext(working_db=db_client, master_db=self.master_db, sbb_idx=self.sbb_idx)
            self.available_dbs.append(cr_data)

    def _reset_cr_data(self, ds: CRContext):
        ds.reset()
        Phase.reset_phase_variables(ds.working_db)

    def flush_all(self):
        """ Flushes all pending/active/available dbs. This effectively 'resets' all databases except master."""
        if self.active_db:
            self._reset_cr_data(self.active_db)
            self.active_db = None
        for s in (self.pending_dbs, self.available_dbs):
            for cr in s:
                self._reset_cr_data(cr)
            s.clear()
        self._setup_dbs()

    def update_master_db(self, should_commit=True) -> List[tuple]:
        """
        Merges the first (leftpop) pending_db to master.

        Returns a list of tuples. There will be one tuple for each contract in self.contracts, and tuples will be of the
        form (contract, status, state). contract will be an instance of ContractTransaction. Status will be a string
        representing the execution status of the contract (fail/succ/ect). State will be a string that represents the
        changes to state made by that contract.
        """
        assert len(self.pending_dbs) > 0, "No pending dbs to update to master!"
        cr_data = self.pending_dbs.popleft()
        assert cr_data.merge_to_common, "CRData not merged to common yet!"

        # TODO this is bad hacky. Only SBB 0 will be able to make these asserts, b/c the db is cleared afterwords.
        # we could defer resetting the db until the last SB calls this, but nvm that for now
        if self.sbb_idx == 0:
            assert Phase.get_phase_variable(cr_data.working_db, Macros.EXECUTION) == self.num_sb_builders, \
                "Execution stage incomplete!"
            assert Phase.get_phase_variable(cr_data.working_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders, \
                "Conflict resolution stage incomplete!"

        if should_commit:
            self.log.notice("Merging common layer to master db")
            CRContext.merge_to_master(working_db=cr_data.working_db, master_db=self.master_db)

        sbb_rep = cr_data.get_subblock_rep()

        self.log.debugv("Resetting CRContext with input hash {}".format(cr_data.input_hash))
        self._reset_cr_data(cr_data)
        self.available_dbs.append(cr_data)

        return sbb_rep

    def submit_contract(self, contract):
        self.publish_code_str(contract.contract_name, contract.sender, contract.code, keep_original=True, scope={
            'rt': {
                'author': contract.sender,
                'sender': contract.sender
            }
        })

    def run_contract(self, contract):
        assert self.active_db, "active_db must be set to run a contract. Did you call start_sub_block?"
        assert self.active_db.input_hash, "Input hash not set...davis u done goofed again"

        result = self._run_contract(contract, contract_idx=self.active_db.next_contract_idx, data=self.active_db)
        self.active_db.add_contract_result(contract, result)

    def _run_contract(self, contract, contract_idx: int, data: CRContext) -> str:
        """ Runs the contract object, and retuns a string representing the result (succ/fail).
        Note: Assumes the BookKeeping info has already been set. """
        # TODO fix this to return result of running as a contract as a Bool as well. This way we can the CRContext
        # to 'revert' the appropriate contract info
        BookKeeper.set_info(sbb_idx=self.sbb_idx, contract_idx=contract_idx, data=data)
        contract_name = contract.contract_name
        metadata = self.get_contract_meta(contract_name)

        try:
            self.execute_code_str(contract.code, scope={
                'rt': {
                    'author': metadata['author'],
                    'sender': contract.sender
                },
                '__contract__': contract_name
            })
            result = SUCC_FLAG
        except Exception as e:
            self.log.warning("Contract failed with error: {} \ncontract obj: {}".format(e, contract))
            # TODO can we get more specific fail messages?
            result = 'FAIL' + ' -- ' + str(e)
            data.rollback_contract(contract_idx)

        return result

    def _rerun_contracts_for_cr_data(self, cr_data: CRContext):
        """ Reruns any contracts in cr_data, if necessary. This should be done before we merge cr_data to common. """
        self.log.info("Rerunning any necessary contracts for CRData with input hash {}".format(cr_data.input_hash))
        for i in cr_data.iter_rerun_indexes():
            result = self._run_contract(cr_data.contracts[i], contract_idx=i, data=cr_data)
            cr_data.update_contract_result(contract_idx=i, result=result)

    def catchup(self):
        raise NotImplementedError('code this up if ur tryna use it u lazy bum')

    def has_available_db(self) -> bool:
        return len(self.available_dbs) > 0

    def start_sub_block(self, input_hash: str):
        if not self.has_available_db():
            raise Exception("Attempted to start a new sub block, but there are no available DBs!")

        self.active_db = self.available_dbs.popleft()
        self.active_db.input_hash = input_hash

    def end_sub_block(self):
        """
        Ends the current sub block, and schedules for it rerun any necessary contracts, and then merge to the common
        layer. Once this rerun and merge is complete, completion_handler is called with the finalized CRContext
        """
        assert self.active_db, "Active db not set! Did you call start_sub_block?"
        self.log.notice("Ending sub block {} which has input hash {}".format(self.sbb_idx, self.active_db.input_hash))

        Phase.incr_phase_variable(self.active_db.working_db, Macros.EXECUTION)

        future = asyncio.ensure_future(self._wait_and_merge_to_common(self.active_db))
        self.pending_futures[self.active_db.input_hash] = {'fut': future, 'data': self.active_db}

        self.pending_dbs.append(self.active_db)
        self.active_db = None  # we really don't care, but might be useful initially for error checking

    async def _wait_and_merge_to_common(self, cr_data: CRContext):
        """
        - Waits for all other SBBs to finish execution. Raises an error if this takes longer than Phase.EXEC_TIMEOUT
        - Waits for all subblocks before it finish conflict resolution. Raises an error if it takes longer than Phase.CR_TIMEOUT
        - If the db is at the top of pending_dbs, we then:
            - Rerun any necessary contracts
            - Merges cr_data to common layer, and then increment the CONFLICT_RESOLUTION phase variable
        - If it is not on the top of pending db's, the merging logic will be called later when merge_to_master is called
        """
        await self._wait_for_execution_stage(cr_data)

        if self.pending_dbs[0] is not cr_data:
            await self._wait_until_top_of_pending(cr_data)

        await self._wait_for_cr_and_merge(cr_data)
        # self.pending_futures[cr_data.input_hash]['fut'].set_result('done')  # TODO fix this its complaining...

    async def _wait_for_cr_and_merge(self, cr_data: CRContext):
        self.log.info("Waiting for other SBBs to finish conflict resolution...")
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.CONFLICT_RESOLUTION, value=self.sbb_idx,
                                            timeout=(len(self.pending_dbs) + 1) * Phase.CR_TIMEOUT)
        self.log.info("Done waiting for other SBBs to finish contract resolution")

        self._rerun_contracts_for_cr_data(cr_data)
        self.log.notice("Merging sbb_{} data to common layer".format(self.sbb_idx))
        cr_data.merge_to_common()
        Phase.incr_phase_variable(cr_data.working_db, Macros.CONFLICT_RESOLUTION)

        self.log.debug("Finished finalizing sub block for input hash {}!".format(cr_data.input_hash))

    async def _wait_until_top_of_pending(self, cr_data: CRContext):
        """ Waits until cr_data is at the top (first element) of self.pending_dbs """
        elapsed = 0
        timeout = Phase.BLOCK_TIMEOUT * len(self.pending_dbs)
        self.log.debug("CRData with input hash {} waiting its turn until its at the top of pending_dbs..."
                       .format(cr_data.input_hash))

        while self.pending_dbs[0] is not cr_data:
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= timeout:
                err_msg = "Exceeded timeout of {} waiting for db with input hash {} to reach top of pending dbs!" \
                          .format(timeout, cr_data.input_hash)
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.info("CRData with input hash {} DONE waiting to be at the top of pending db!".format(cr_data.input_hash))

    async def _wait_for_execution_stage(self, cr_data: CRContext):
        self.log.info("Waiting for other SBBs to finish execution...")
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.EXECUTION, value=self.num_sb_builders,
                                            timeout=(len(self.pending_dbs) + 1) * Phase.EXEC_TIMEOUT)
        self.log.info("Done waiting for other SBBs to finish execution")

    async def _wait_for_phase_variable(self, db: redis.StrictRedis, key: str, value: int, timeout: int):
        elapsed = 0
        while Phase.get_phase_variable(db, key) != value:
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= timeout:
                err_msg = "Client with sbb_idx {} exceeded timeout of {} waiting for phase key {} to reach {}! " \
                          "Current conflict resolution phase value: {}" \
                    .format(self.sbb_idx, elapsed, key, value,
                            Phase.get_phase_variable(db, key))
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.debug("Waited a total of {} seconds for phase variable {} to reach value {}".format(elapsed, key, value))
