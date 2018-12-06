import time, asyncio, ujson as json, redis, traceback
from seneca.libs.logger import get_logger
from seneca.engine.interface import SenecaInterface
from seneca.constants.config import *
from seneca.engine.conflict_resolution import CRContext
from seneca.engine.book_keeper import BookKeeper
from seneca.engine.util import module_path_for_contract
from collections import deque, defaultdict
from typing import Callable, List


SUCC_FLAG = 'SUCC'


class Macros:
    # TODO we need to make sure these keys dont conflict with user stuff in the common layer. I.e. users cannot be
    # creating keys named '_execution' or '_conflict_resolution'
    EXECUTION = '_execution_phase'
    CONFLICT_RESOLUTION = '_conflict_resolution_phase'
    RESET = "_reset_phase"

    ALL_MACROS = [EXECUTION, CONFLICT_RESOLUTION]


class Phase:
    EXEC_TIMEOUT = 14  # Number of seconds client will wait for other clients to finish execution phase
    CR_TIMEOUT = 14  # Number of seconds client will wait for other clients to finish conflict resolution phase
    BLOCK_TIMEOUT = 30  # Number of seconds a pending db will wait until it is at the top (first element) of pending_dbs
    AVAIL_DB_TIMEOUT = 60  # How long the client will wait for a DB to become available when executing a SB
    POLL_INTERVAL = 0.5  # Poll for Phase changes every POLL_INTERVAL seconds

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

        # pending_futures tracks active db's that are waiting for other SBBs to finish CR/execution
        # it is a map of input hashes -> {'fut': asyncio.Future, 'data': CRContext, ...}
        self.pending_futures = {}

        # queued_futures tracks execute_sb calls that cannot run immediately because there are no available dbs
        # it is a map of input hashes -> asyncio.Future
        self.queued_futures = {}

        self._setup_dbs()

    def _setup_dbs(self):
        self.master_db = redis.StrictRedis(host='localhost', port=self.port, db=MASTER_DB, password=self.password)
        for db_num in range(self.max_number_workers):
            db_client = redis.StrictRedis(host='localhost', port=self.port, db=db_num+DB_OFFSET, password=self.password)
            cr_data = CRContext(working_db=db_client, master_db=self.master_db, sbb_idx=self.sbb_idx)
            self.available_dbs.append(cr_data)

    def flush_all(self):
        """ Flushes all pending/active/available dbs. This effectively 'resets' all databases except master."""
        if self.active_db:
            self.active_db.reset(hard_reset=True)
            self.active_db = None
        for s in (self.pending_dbs, self.available_dbs):
            for cr in s:
                cr.reset(hard_reset=True)
            s.clear()

        for input_hash in self.pending_futures:
            self.pending_futures[input_hash]['fut'].cancel()
            if self.pending_futures[input_hash]['merge_fut']:
                self.pending_futures[input_hash]['merge_fut'].cancel()
        self.pending_futures.clear()

        for input_hash in self.queued_futures:
            self.queued_futures[input_hash].cancel()
        self.queued_futures.clear()

        # does it leak some dbs?
        self._setup_dbs()

    def _update_master_db(self, expected_data: CRContext=None):
        assert len(self.pending_dbs) > 0, "No pending dbs to update to master!"

        cr_data = self.pending_dbs.popleft()
        if expected_data:
            assert expected_data == cr_data, "Updated master db with expected cr data with input hash {}, but leftpop " \
                                             "cr data has input hash {}!".format(expected_data.input_hash, cr_data.input_hash)
        input_hash = cr_data.input_hash
        assert input_hash is not None, "Input hash is None! Dev error this should not happen"
        assert cr_data.merged_to_common, "CRData not merged to common yet!"

        self.log.notice("Updating master db for input_hash {}".format(cr_data.input_hash))  # TODO change log lvl

        if self.sbb_idx == 0:
            assert Phase.get_phase_variable(cr_data.working_db, Macros.EXECUTION) == self.num_sb_builders, \
                "Execution stage incomplete!"
            assert Phase.get_phase_variable(cr_data.working_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders, \
                "Conflict resolution stage incomplete!"

            self.log.important("Merging common layer to master db")
            CRContext.merge_to_master(working_db=cr_data.working_db, master_db=self.master_db)

        self.log.debugv("Resetting run data for input hash {}".format(cr_data.input_hash))
        cr_data.reset_run_data()
        Phase.incr_phase_variable(cr_data.working_db, Macros.RESET)

        # Only hard reset (meaning flush redis data) if all other SBBs have finished updating to master db
        if Phase.get_phase_variable(cr_data.working_db, Macros.RESET) == self.num_sb_builders:
            self.log.debug("RESET phase finished. Hard resetting db for input hash {}".format(input_hash))
            cr_data.reset(hard_reset=True)
        else:
            self.log.debugv("Soft resetting db for input hash {}".format(input_hash))
            cr_data.reset(hard_reset=False)

        self.pending_futures.pop(input_hash)
        self.available_dbs.append(cr_data)

    def update_master_db(self):
        # If no pending dbs to sync to master db, return
        # NOTE: For dev, we raise a proper exception. This should not happen. --davis
        if len(self.pending_dbs) == 0:
            raise Exception("Attempted to update_master_db, but there are no pending_dbs")
            # self.log.warning("Attempted to update_master_db, but there are no pending_dbs")
            # return

        cr_data = self.pending_dbs[0]
        input_hash = cr_data.input_hash
        cr_finished = Phase.get_phase_variable(cr_data.working_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders

        assert input_hash in self.pending_futures, "Input hash {} not in pending_futures {}".format(input_hash, self.pending_futures)
        assert cr_data == self.pending_futures[input_hash]['data'], "something has gone horribly wrong"

        if not cr_finished:
            self.log.info(("Deferring merge for input_hash {}".format(input_hash)))
            if self.pending_futures[cr_data.input_hash]['complete']:
                self.log.debugv("Future already complete! Adding new future to update master db when ready")
                # fut = self._ensure_future(self._wait_to_update_master_db(cr_data))
                fut = self._ensure_future(self._wait_to_update_master_db(cr_data))
                self.pending_futures[cr_data.input_hash]['merge_fut'] = fut
            else:
                self.log.debugv("CRContext future not yet complete. Setting merge flag to true.")
                self.pending_futures[cr_data.input_hash]['merge'] = True
        else:
            self._update_master_db(expected_data=cr_data)

    def submit_contract(self, contract):
        self.publish_code_str(contract.contract_name, contract.sender, contract.code, scope={
            'rt': {
                'author': contract.sender,
                'sender': contract.sender,
                'contract': contract.contract_name
            }
        })

    def run_contract(self, contract):
        assert self.active_db, "active_db must be set to run a contract. Did you call _start_sb?"
        assert self.active_db.input_hash, "Input hash not set...davis u done goofed again"

        result = self._run_contract(contract, contract_idx=self.active_db.next_contract_idx, data=self.active_db)
        self.active_db.add_contract_result(contract, result)

    def _run_contract(self, contract, contract_idx: int, data: CRContext) -> str:
        """ Runs the contract object, and retuns a string representing the result (succ/fail).
        Note: Assumes the BookKeeping info has already been set. """
        BookKeeper.set_info(sbb_idx=self.sbb_idx, contract_idx=contract_idx, data=data)

        try:
            # Super sketch hack to differentiate between ContractTransactions and PublishTransactions
            # TODO not this pls
            if hasattr(contract, 'contract_code'):
                author = contract.sender
                self.publish_code_str(fullname=contract.contract_name, author=author,
                                      code_str=contract.contract_code)
            else:
                mod_path = module_path_for_contract(contract)
                self.execute_function(module_path=mod_path, sender=contract.sender,
                                      stamps=contract.stamps_supplied, **contract.kwargs)
            result = SUCC_FLAG

        except Exception as e:
            self.log.warning("Contract failed with error: {} \ncontract obj: {}".format(e, contract))
            result = 'FAIL' + ' -- ' + str(e)
            data.rollback_contract(contract_idx)

        return result

    def _rerun_contracts_for_cr_data(self, cr_data: CRContext):
        """ Reruns any contracts in cr_data, if necessary. This should be done before we merge cr_data to common. """
        self.log.info("Rerunning any necessary contracts for CRData with input hash {}".format(cr_data.input_hash))
        for i in cr_data.iter_rerun_indexes():
            result = self._run_contract(cr_data.contracts[i], contract_idx=i, data=cr_data)
            cr_data.update_contract_result(contract_idx=i, result=result)

    def _can_start_next_sb(self) -> bool:
        """
        Returns True if we this client can start the next subblock, and False otherwise. A client can start a sb if:
        - There is no active db set
        - There is at least 1 available_db
        - All other SBBs are finished with that first available_db (meaning it has been hard reset and merged to master)
        """
        return (not self.active_db and len(self.available_dbs) > 0) and \
               (Phase.get_phase_variable(self.available_dbs[0].working_db, Macros.RESET) == 0)

    def execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        """
        Begins execution of a sub-block with the given list of contracts and the input hash. Once execution
        and conflict resolution is finished, completion_handler is called with a CRContext instance as the only arg.

        If there are no available db's, AND the we have exceeded the allowed nubmer of queued db's, this will return
        False. Otherwise, if a DB is immediately available, or if there is room in the queue, this method will return
        True.
        """
        assert input_hash not in self.pending_futures, "SB with input hash {} is already pending!".format(input_hash)
        assert input_hash not in self.queued_futures, "SB with input hash {} is already queued!".format(input_hash)
        assert input_hash is not None, "Input hash cannot be None!"

        if self._can_start_next_sb():
            self._execute_sb(input_hash, contracts, completion_handler)

        else:
            if len(self.queued_futures) >= MAX_SB_QUEUE_SIZE:
                self.log.warning("Maximum number ({}) of queueud sub-blocks has been reached! Not scheduling sub-block "
                                 "execution for input hash {}. All queued futures: {}"
                                 .format(MAX_SB_QUEUE_SIZE, input_hash, self.queued_futures))
                return False

            self.log.debugv("No available dbs. Queueing up future to execute sb for input hash {}".format(input_hash))
            fut = self._ensure_future(self._wait_and_execute_sb(input_hash, contracts, completion_handler))
            self.queued_futures[input_hash] = fut

        return True

    def _execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        self.log.debug("Executing sub block for input hash {}".format(input_hash))
        self.queued_futures.pop(input_hash, None)

        self._start_sb(input_hash)
        for c in contracts:
            self.run_contract(c)
        self._end_sb(completion_handler)

    def _start_sb(self, input_hash: str):
        assert self.active_db is None, "Attempted to _start_sb, but active_db is already set! Did you end the " \
                                       "previous subblock with _end_sb?"
        assert self._can_start_next_sb(), "Attempted to start a new sub block, but cannot start next sb!!! Dev error!"

        self.log.debug("Starting sb with input hash {}".format(input_hash))
        self.active_db = self.available_dbs.popleft()
        self.active_db.input_hash = input_hash

    def _end_sb(self, completion_handler: Callable[[CRContext], None]):
        """
        Ends the current sub block. Specifically, this method:
         - Increments the EXECUTION phase variable
         - Pushes active_db onto the top of the pending_db stack
         - Ensures the _wait_and_merge_to_common future (see doc string on that func for more details)
         - Once the _wait_and_merge_to_common future is done, the callback is trigger
        """
        assert self.active_db, "Active db not set! Did you call _start_sb?"
        self.log.info("Ending sub block {} which has input hash {}".format(self.sbb_idx, self.active_db.input_hash))

        Phase.incr_phase_variable(self.active_db.working_db, Macros.EXECUTION)

        future = self._ensure_future(self._wait_and_merge_to_common(self.active_db, completion_handler))
        self.pending_futures[self.active_db.input_hash] = {'fut': future, 'data': self.active_db, 'merge': False,
                                                           'complete': False, 'merge_fut': None}

        self.pending_dbs.append(self.active_db)
        self.active_db = None  # we really don't care, but might be useful initially for error checking

    async def _wait_and_execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        await self._wait_for_available_db()
        self._execute_sb(input_hash, contracts, completion_handler)

    async def _wait_and_merge_to_common(self, cr_data: CRContext, completion_handler: Callable[[CRContext], None]):
        """
        - Waits for all other SBBs to finish execution. Raises an error if this takes longer than Phase.EXEC_TIMEOUT
        - Waits for this cr_data to be first in line in 'pending_dbs' (bottom of stack)
        - Waits for all subblocks before it finish conflict resolution. Raises an error if it takes longer than Phase.CR_TIMEOUT
        - Starts conflict resolution, which involves:
            - Rerun any necessary contracts
            - Merges cr_data to common layer, and then increment the CONFLICT_RESOLUTION phase variable
        - If the 'merge' flag is set by an earlier update_master_db call, then this is done next
        """
        await self._wait_for_execution_stage(cr_data)

        if self.pending_dbs[0] is not cr_data:
            await self._wait_until_top_of_pending(cr_data)

        await self._wait_for_cr_and_merge(cr_data)

        self.log.notice("Invoking completion handler for sub block with input hash {}".format(cr_data.input_hash))
        completion_handler(cr_data)

        # Dev sanity check
        assert cr_data.input_hash in self.pending_futures, "Input hash {} removed from pending futures {}!"\
                                                           .format(cr_data.input_hash, self.pending_futures)

        if self.pending_futures[cr_data.input_hash]['merge']:
            self.log.debugv("Merge flag set to true for sbb with input hash {}".format(cr_data.input_hash))
            await self._wait_to_update_master_db(cr_data)
        else:
            self.pending_futures[cr_data.input_hash]['complete'] = True

    async def _wait_to_update_master_db(self, cr_data: CRContext):
        # If this is the first sub-block, then we are responsible for merging to master db. Thus we must wait
        # for everyone to finish conflict resolution before we merge to master.
        if self.sbb_idx == 0:
            await self._wait_for_everybody_cr(cr_data)
        self._update_master_db(expected_data=cr_data)

    async def _wait_for_available_db(self):
        elapsed = 0
        while not self._can_start_next_sb():
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= Phase.AVAIL_DB_TIMEOUT:
                err_msg = "Exceeded timeout of {} waiting for an available db!".format(Phase.AVAIL_DB_TIMEOUT)
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.debugv("Waited a total of {} seconds for a db to become available".format(elapsed))

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
        # TODO technically this 'wait' can be triggered reactively when we leftpop pending_dbs in merge_to_master
        # This is an optimization we can do later
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
        self.log.info("Waiting for other SBBs to finish execution (input_hash={})".format(cr_data.input_hash))
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.EXECUTION, value=self.num_sb_builders,
                                            timeout=(len(self.pending_dbs) + 1) * Phase.EXEC_TIMEOUT)
        self.log.info("Done waiting for other SBBs to finish execution (input_hash={})".format(cr_data.input_hash))

    async def _wait_for_everybody_cr(self, cr_data: CRContext):
        self.log.info("Waiting for conflict resolution to finish for ALL sub blocks (input_hash={})".format(cr_data.input_hash))
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.CONFLICT_RESOLUTION,
                                            value=self.num_sb_builders, timeout=Phase.CR_TIMEOUT)
        self.log.info("Conflict resolution complete for ALL sub blocks (input_hash={})".format(cr_data.input_hash))

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

    def _ensure_future(self, coro) -> asyncio.Future:
        """
        A small wrapper around asyncio.ensure_future to catch any error and log them before raising them. We do this
        because sometimes asyncio does not properly raise the exceptions, causing coroutines to sometimes fail
        silently.
        """
        async def _safe_ensure_future():
            try:
                return await coro
            except Exception as e:
                self.log.fatal("\nError caught in coro {}!\n{}\n".format(coro, traceback.format_exc()))
                raise e

        return asyncio.ensure_future(_safe_ensure_future())
