import asyncio
import time
from seneca.logger import get_logger
from seneca.execution.executor import Executor
from seneca.db.cr.cache import CRCache
from seneca import config
from seneca.db.cr.transaction_bag import TransactionBag
from seneca.db.driver import ContractDriver
from collections import deque
from typing import Callable
import traceback



class SubBlockClient:
    def __init__(self, sbb_idx, num_sbb, loop=None):
        name = self.__class__.__name__ + "[sbb-{}]".format(sbb_idx)
        self.log = get_logger(name)

        self.num_sbb = num_sbb
        self.sbb_idx

        self.master_db = ContractDriver()
        self.current_cache = None
        self.available_caches = deque() # LIFO
        self.pending_caches = deque() # FIFO
        self.executor = Executor()
        for i in config.NUM_CACHES:
            self.available_caches.append(CRCache(config.DB_OFFSET+i, self.master_db,
                                                 self.sbb_idx, self.num_sbb,
                                                 self.executor))

    ###################
    ## EXTERNAL APIS ##
    ###################

    def flush_all(self):
        """
        Convenience function for testing

        FULLY SYNCHRONOUS

        :return:
        """
        intervals = config.CLEAN_TIMEOUT/config.POLL_INTERVAL
        for cache in self.pending_caches:
            cache.discard()
            for i in range(intervals):
                cache.sync_reset()
                if cache.state == 'CLEAN':
                    break
                time.sleep(config.POLL_INTERVAL)

            if i == intervals-1:
                raise TimeoutError("Timed out waiting for all subblocks to sync cleanup on cache #{}".format(cache.idx))
            self.available_caches.append(cache)

        self.pending_caches.clear()

    def execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        return

    def update_master_db(self):
        return

    ######################
    ## INTERNAL METHODS ##
    ######################


class SenecaClient:


    def __init__(self, sbb_idx, num_sbb, loop=None, *args, **kwargs):
        # TODO do we even need to bother with the concurrent_mode flag? We are treating that its always true --davis
        super().__init__(*args, **kwargs)

        name = self.__class__.__name__ + "[sbb-{}]".format(sbb_idx)
        self.log = get_logger(name)


        self.loop = loop or asyncio.get_event_loop()

        self.sbb_idx = sbb_idx
        self.num_sb_builders = num_sbb
        self.max_number_workers = NUM_CACHES

        self.master_db = None  # A ledis.Ledis instance
        self.active_db = None  # Set to a CRContext instance
        self.available_dbs = deque()  # List of CRContext instances (popped LIFO)
        self.pending_dbs = deque()  # List of CRContext instances (popped FIFO)

        self.executor = Executor(metering=False, production=True)

        # pending_futures tracks active db's that are waiting for other SBBs to finish CR/execution
        # it is a map of input hashes -> {'fut': asyncio.Future, 'data': CRContext, ...}
        self.pending_futures = {}

        # queued_futures tracks execute_sb calls that cannot run immediately because there are no available dbs
        # it is a deque of dicts, containing keys 'input_hash': str, and 'fut': asyncio.Future
        self.queued_futures = deque()

        self._setup_dbs()

        self.log.important3("---- SENECA CLIENT CREATION FINISHED -----")

    def _setup_dbs(self):
        self.master_db = DatabaseDriver(host='localhost', db=MASTER_DB)
        for db_num in range(self.max_number_workers):
            db_client = DatabaseDriver(host='localhost', db=db_num+DB_OFFSET)
            Phase.reset_keys(db_client)
            cr_data = CRContext(working_db=db_client, master_db=self.master_db, sbb_idx=self.sbb_idx)
            self.available_dbs.append(cr_data)

    def flush_all(self):
        """ Flushes all pending/active/available dbs. This effectively 'resets' all databases except master."""
        if self.active_db:
            self.active_db.reset_db()
            self.active_db.reset_run_data()
            self.active_db = None
        for s in (self.pending_dbs, self.available_dbs):
            for cr in s:
                cr.reset_db()
                cr.reset_run_data()
            s.clear()

        for input_hash in self.pending_futures:
            self.pending_futures[input_hash]['fut'].cancel()
            if self.pending_futures[input_hash]['merge_fut']:
                self.pending_futures[input_hash]['merge_fut'].cancel()
        self.pending_futures.clear()

        for data in self.queued_futures:
            data['fut'].cancel()
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

        self.log.notice("Updating master db for CR data {}".format(cr_data))

        futs = self.pending_futures.pop(input_hash, None)

        if self.sbb_idx == 0:
            assert Phase.get(cr_data.working_db, Macros.EXECUTION) == self.num_sb_builders, \
                "Execution stage incomplete!"
            assert Phase.get(cr_data.working_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders, \
                "Conflict resolution stage incomplete!"

            self.log.important("Merging common layer to master db (input_hash={})".format(cr_data.input_hash))
            CRContext.merge_to_master(working_db=cr_data.working_db, master_db=self.master_db)

        self.log.debugv("Resetting run data for input hash {}".format(cr_data.input_hash))
        cr_data.reset_run_data()

        # Only hard reset_db (meaning flush ledis data) if all other SBBs have finished updating to master db
        reset_var = Phase.incr(cr_data.working_db, Macros.RESET)  # this will do an atomic incr and get
        if reset_var == self.num_sb_builders:
            self.log.debug("RESET phase finished. Resetting db for input hash {}".format(input_hash))
            cr_data.reset_db()

        cr_data.assert_reset()  # Dev check. Make sure cr_context has been properly reset_db

        self.available_dbs.append(cr_data)

    def update_master_db(self):
        # If no pending dbs to sync to master db, return
        # NOTE: For dev, we raise a proper exception. This should not happen. --davis
        if len(self.pending_dbs) == 0:
            # raise Exception("Attempted to update_master_db, but there are no pending_dbs")
            self.log.warning("Attempted to update_master_db, but there are no pending_dbs")
            return

        cr_data = self.pending_dbs[0]
        input_hash = cr_data.input_hash
        cr_finished = Phase.get(cr_data.working_db, Macros.CONFLICT_RESOLUTION) == self.num_sb_builders
        self.log.info("Attempting to merge to master db for input hash {}".format(input_hash))

        assert input_hash in self.pending_futures, "Input hash {} not in pending_futures {}".format(input_hash, self.pending_futures)
        assert cr_data == self.pending_futures[input_hash]['data'], "something has gone horribly wrong"

        if not cr_finished:
            self.log.info(("Deferring merge for {}".format(cr_data)))
            if self.pending_futures[input_hash]['complete']:
                self.log.debugv("Future already complete! Adding new future to update master db when ready")
                fut = self._ensure_future(self._wait_to_update_master_db(cr_data))
                self.pending_futures[input_hash]['merge_fut'] = fut
            else:
                self.log.debugv("CRContext future not yet complete. Setting merge flag to true.")
                self.pending_futures[input_hash]['merge'] = True
        else:
            self.log.info("Merging immediately for {}".format(cr_data))
            self._update_master_db(expected_data=cr_data)

    def skip_current_db(self):
        if len(self.pending_dbs) == 0:
            self.log.warning("skip_current_db called, but there are no pending dbs! Returning.")
            return

        cr_data = self.pending_dbs.popleft()
        cr_dict = self.pending_futures.pop(cr_data.input_hash)

        assert cr_dict['merge'] is False, "tried to skip current db, but merge flag set to true for CR {} with pending" \
                                          " futures dict {}".format(cr_data, cr_dict)
        cr_dict['fut'].cancel()

    def submit_contract(self, contract):
        self.publish_code_str(contract.contract_name, contract.sender, contract.code)

    # def run_contract(self, contract):
    #     assert self.active_db, "active_db must be set to run a contract. Did you call _start_sb?"
    #     assert self.active_db.input_hash, "Input hash not set...davis u done goofed again"
    #
    #     data = self.active_db
    #     contract_idx = data.next_contract_idx
    #
    #     result = self._run_contract(contract, contract_idx=contract_idx, data=data)
    #     self.active_db.add_contract_result(contract, result)
    #
    #     # DEBUG
    #     kwargs = 'contract_name=' + contract.contract_name if hasattr(contract, 'contract_code') else contract.kwargs
    #     self.log.notice("[EXEC PHASE #{}] exec from sender {} with kwargs {} resulted in state {}"
    #                   .format(contract_idx, contract.sender, kwargs, data.get_state_for_idx(contract_idx)))
    #     # END DEBUG
    #
    # def _run_contract(self, contract, contract_idx: int, data: CRContext) -> str:
    #     """ Runs the contract object, and retuns a string representing the result (succ/fail).
    #     Note: Assumes the BookKeeping info has already been set. """
    #     # Development sanity checks. data passed in should either be the active_db (if we are in execution phase)
    #     # or it should be next in line in pending_dbs if we are in CR phase
    #     assert data is self.active_db or data is self.pending_dbs[0], \
    #         "Data {} is not active db {} or next pending db {}".format(data, self.active_db, self.pending_dbs[0])
    #
    #     try:
    #         BookKeeper.set_cr_info(sbb_idx=self.sbb_idx, contract_idx=contract_idx, data=data, rt={
    #             'contract': contract.contract_name
    #         })
    #         data.locked = False
    #
    #         # raghu todo ? clarify with Davis - this is a transaction which is also a contract ? if so, txn.sender is what is inside contract.sender while contract.contract_name and contract.func_name are the previously submitted code ?
    #         # and if this is a submit_contract, contract_name is smart_contract, func_name = submit_contract, kwargs will have contract_name for new contract and code-str and contract.sender is the author of new contract?
    #         run_info = self.execute_function(contract.contract_name, contract.func_name, contract.sender,
    #                                          contract.stamps_supplied, kwargs=contract.kwargs)
    #
    #         # The following is just for debug info
    #         stamps_spent = run_info['stamps_used']
    #         self.log.spam("Running contract from sender {} used {} stamps and returned run_info: {}"
    #                       .format(contract.sender, stamps_spent, run_info))
    #
    #         result = SUCC_FLAG
    #
    #     except Exception as e:
    #         # TODO -- change this log level for production, as we will get spammed like nuts when contracts fail
    #         self.log.warning("Contract failed with error:\n{} \ncontract obj: {}".format(traceback.format_exc(), contract))
    #         result = 'FAIL' + ' -- ' + str(e)
    #         data.rollback_contract(contract_idx)
    #
    #     finally:
    #         data.locked = True
    #
    #     return result

    def _rerun_transactions_for_cr_data(self, cr_data: CRContext):
        """ Reruns any contracts in cr_context, if necessary. This should be done before we merge cr_context to common. """
        # This cr_context should be next in line in pending_dbs if we are rerunning contracts
        assert self.pending_dbs[0] is cr_data, "cr_context {} is not first in line in pending_dbs! First is {}"\
                                               .format(cr_data, self.pending_dbs[0])

        self.log.notice("Rerunning any necessary contracts for CRData with input hash {}".format(cr_data.input_hash))

        bag = TransactionBag([(i, cr_data.contracts[i]) for i in cr_data.iter_rerun_indexes()], cr_data)
        self._execute_bag(bag, should_update=True)

    def _execute_bag(self, bag: TransactionBag, should_update=False):
        for idx, res in self.executor.execute_bag(bag).items():
            status_code, output = res['status_code'], res['result']

            if status_code == 1:
                self.log.warning("Contract {} failed with error:\n{}".format(bag.get_tx_at_idx(idx), output))
                bag.cr_context.rollback_contract(idx)
                flag = "FAIL -- {}".format(output)
            else:
                flag = "SUCC"  # todo attach the output also?? why do we even need the output actually?

            if should_update:
                bag.cr_context.update_contract_result(bag.get_tx_at_idx(idx), flag)
            else:
                bag.cr_context.add_contract_result(bag.get_tx_at_idx(idx), flag)

    def _can_start_next_sb(self) -> bool:
        """
        Returns True if we this client can start the next subblock, and False otherwise. A client can start a sb if:
        - There is no active db set
        - There is at least 1 available_db
        - All other SBBs are finished with that first available_db (meaning it has been hard reset_db and merged to master)
        """
        return (not self.active_db and len(self.available_dbs) > 0) and \
               (Phase.get(self.available_dbs[0].working_db, Macros.RESET) == 0)

    def execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        """
        Begins execution of a sub-block with the given list of contracts and the input hash. Once execution
        and conflict resolution is finished, completion_handler is called with a CRContext instance as the only arg.

        If there are no available db's, AND the we have exceeded the allowed nubmer of queued db's, this will return
        False. Otherwise, if a DB is immediately available, or if there is room in the queue, this method will return
        True.
        """
        assert input_hash not in self.pending_futures, "SB with input hash {} is already pending!".format(input_hash)
        for data in self.queued_futures:
            if data['input_hash'] == input_hash:
                raise Exception("Input hash {} already in queued futures {}".format(input_hash, self.queued_futures))
        assert input_hash is not None, "Input hash cannot be None!"

        if self._can_start_next_sb():
            self._execute_sb(input_hash, contracts, completion_handler)

        else:
            if len(self.queued_futures) >= MAX_SB_QUEUE_SIZE:
                self.log.warning("Maximum number ({}) of queueud sub-blocks has been reached! Not scheduling sub-block "
                                 "execution for input hash {}. All queued futures: {}"
                                 .format(MAX_SB_QUEUE_SIZE, input_hash, self.queued_futures))
                return False

            self.log.info("No available dbs. Queueing up future to execute sb for input hash {}".format(input_hash))
            fut = self._ensure_future(self._wait_and_execute_sb(input_hash, contracts, completion_handler))
            self.queued_futures.append({'input_hash': input_hash, 'fut': fut})

        return True

    def _execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        self.log.info(">>> Executing sub block for input hash {} with {} txs >>>".format(input_hash, len(contracts)))

        self._start_sb(input_hash)

        bag = TransactionBag(list(enumerate(contracts)), self.active_db)
        self._execute_bag(bag, should_update=False)

        self._end_sb(completion_handler)

    def _start_sb(self, input_hash: str):
        assert self.active_db is None, "Attempted to _start_sb, but active_db is already set! Did you end the " \
                                       "previous subblock with _end_sb?"
        assert self._can_start_next_sb(), "Attempted to start a new sub block, but cannot start next sb!!! Dev error!"

        self.active_db = self.available_dbs.popleft()
        self.active_db.assert_reset()  # Dev checks, make sure the CRContext has been properly reset_db

        self.active_db.input_hash = input_hash
        self.log.important("Starting sb with CRData {}".format(self.active_db))

    def _end_sb(self, completion_handler: Callable[[CRContext], None]):
        """
        Ends the current sub block. Specifically, this method:
         - Increments the EXECUTION phase variable
         - Pushes active_db onto the top of the pending_db stack
         - Ensures the _wait_and_merge_to_common future (see doc string on that func for more details)
         - Once the _wait_and_merge_to_common future is done, the callback is trigger
        """
        assert self.active_db, "Active db not set! Did you call _start_sb?"
        self.log.info("<<< Ending sub block for input hash {} <<<".format(self.active_db.input_hash))

        Phase.incr(self.active_db.working_db, Macros.EXECUTION)

        future = self._ensure_future(self._wait_and_merge_to_common(self.active_db, completion_handler))
        self.pending_futures[self.active_db.input_hash] = {'fut': future, 'data': self.active_db, 'merge': False,
                                                           'complete': False, 'merge_fut': None}

        self.pending_dbs.append(self.active_db)
        self.active_db = None  # we really don't care, but might be useful initially for error checking

    async def _wait_and_execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[CRContext], None]):
        await self._wait_for_available_db(input_hash)

        assert self.queued_futures[0]['input_hash'] == input_hash, "Input hash {} does not match next queued hash {}" \
            .format(input_hash, self.queued_futures[0]['input_hash'])
        self.queued_futures.popleft()

        self._execute_sb(input_hash, contracts, completion_handler)

    async def _wait_and_merge_to_common(self, cr_data: CRContext, completion_handler: Callable[[CRContext], None]):
        """
        - Waits for all other SBBs to finish execution. Raises an error if this takes longer than Phase.EXEC_TIMEOUT
        - Waits for this cr_context to be first in line in 'pending_dbs' (bottom of stack)
        - Waits for all subblocks before it finish conflict resolution. Raises an error if it takes longer than Phase.CR_TIMEOUT
        - Starts conflict resolution, which involves:
            - Rerun any necessary contracts
            - Merges cr_context to common layer, and then increment the CONFLICT_RESOLUTION phase variable
        - If the 'merge' flag is set by an earlier update_master_db call, then this is done next
        """
        await self._wait_for_execution_stage(cr_data)

        if self.pending_dbs[0] is not cr_data:
            await self._wait_until_top_of_pending(cr_data)

        await self._wait_for_cr_and_merge(cr_data)

        self.log.notice("Invoking completion handler for sub block with data {}".format(cr_data))
        completion_handler(cr_data)

        # Dev sanity check
        assert cr_data.input_hash in self.pending_futures, "Input hash {} removed from pending futures {}!"\
                                                           .format(cr_data.input_hash, self.pending_futures)

        if self.pending_futures[cr_data.input_hash]['merge']:
            self.log.debugv("Merge flag set to true for {}".format(cr_data))
            await self._wait_to_update_master_db(cr_data)
        else:
            self.pending_futures[cr_data.input_hash]['complete'] = True

    async def _wait_to_update_master_db(self, cr_data: CRContext):
        # If this is the first sub-block, then we are responsible for merging to master db. Thus we must wait
        # for everyone to finish conflict resolution before we merge to master.
        if self.sbb_idx == 0:
            await self._wait_for_everybody_cr(cr_data)
        self._update_master_db(expected_data=cr_data)

    async def _wait_for_available_db(self, input_hash: str):
        elapsed = 0
        while not (self._can_start_next_sb() and self.queued_futures[0]['input_hash'] == input_hash):
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= Phase.AVAIL_DB_TIMEOUT:
                err_msg = "Exceeded timeout of {} waiting for an available db for input hash {}!"\
                          .format(Phase.AVAIL_DB_TIMEOUT, input_hash)
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.debugv("Waited a total of {} seconds for a db to become available for input hash {}"
                        .format(elapsed, input_hash))

    async def _wait_for_cr_and_merge(self, cr_data: CRContext):
        if not self.concurrency:
            self.log.debug("Concurrent mode disabled. Skipping wait for conflict resolution")
            return

        self.log.debug("Waiting for other SBBs to finish conflict resolution ({})...".format(cr_data))
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.CONFLICT_RESOLUTION, value=self.sbb_idx,
                                            timeout=(len(self.pending_dbs) + 1) * Phase.CR_TIMEOUT)
        self.log.debug("Done waiting for other SBBs to finish conflict resolution ({})".format(cr_data))

        self._rerun_transactions_for_cr_data(cr_data)
        self.log.info("Merging sbb_{} data to common layer ({})".format(self.sbb_idx, cr_data))
        cr_data.merge_to_common()

        self.log.debugv("Finished merging to common layer for CR {}. Incrementing CR Phase var.".format(cr_data))
        Phase.incr(cr_data.working_db, Macros.CONFLICT_RESOLUTION)

    async def _wait_until_top_of_pending(self, cr_data: CRContext):
        """ Waits until cr_context is at the top (first element) of self.pending_dbs """
        # TODO technically this 'wait' can be triggered reactively when we leftpop pending_dbs in merge_to_master
        # This is an optimization we can do later
        elapsed = 0
        timeout = Phase.BLOCK_TIMEOUT * len(self.pending_dbs)
        self.log.debug("CRData {} waiting its turn until its at the top of pending_dbs..."
                       .format(cr_data))

        while self.pending_dbs[0] is not cr_data:
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= timeout:
                err_msg = "Exceeded timeout of {} waiting for cr data {} to reach top of pending dbs!" \
                          .format(timeout, cr_data)
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.debug("CRData {} DONE waiting to be at the top of pending db!".format(cr_data))

    async def _wait_for_execution_stage(self, cr_data: CRContext):
        self.log.debug("Waiting for other SBBs to finish execution ({})".format(cr_data))
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.EXECUTION, value=self.num_sb_builders,
                                            timeout=(len(self.pending_dbs) + 1) * Phase.EXEC_TIMEOUT)
        self.log.debug("Done waiting for other SBBs to finish execution ({})".format(cr_data))

    async def _wait_for_everybody_cr(self, cr_data: CRContext):
        self.log.debug("Waiting for conflict resolution to finish for ALL sub blocks ({})".format(cr_data))
        await self._wait_for_phase_variable(db=cr_data.working_db, key=Macros.CONFLICT_RESOLUTION,
                                            value=self.num_sb_builders, timeout=Phase.CR_TIMEOUT)
        self.log.debug("Conflict resolution complete for ALL sub blocks ({})".format(cr_data))

    async def _wait_for_phase_variable(self, db: DatabaseDriver, key: str, value: int, timeout: int):
        elapsed = 0
        while Phase.get(db, key) != value:
            await asyncio.sleep(Phase.POLL_INTERVAL)
            elapsed += Phase.POLL_INTERVAL

            if elapsed >= timeout:
                err_msg = "Client with sbb_idx {} exceeded timeout of {} waiting for phase key {} to reach {}!\n" \
                          "Current {} value: {}\nDB Number: {}" \
                          .format(self.sbb_idx, elapsed, key, value, key, Phase.get(db, key),
                                  db.connection_pool.connection_kwargs['db'])
                self.log.fatal(err_msg)
                raise Exception(err_msg)

        self.log.spam("Waited a total of {} seconds for phase variable {} to reach value {}".format(elapsed, key, value))

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
                if type(e) is asyncio.CancelledError:
                    self.log.warning("Coro {} cancelled.".format(coro))
                else:
                    self.log.fatal("\nError caught in coro {}!\n{}\n".format(coro, traceback.format_exc()))
                    raise e

        return asyncio.ensure_future(_safe_ensure_future())
