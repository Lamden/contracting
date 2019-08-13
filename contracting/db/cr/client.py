import asyncio
from contracting.logger import get_logger
from contracting.execution.executor import Executor
from contracting.db.cr.cache import CRCache
from contracting import config
from contracting.db.cr.transaction_bag import TransactionBag
from contracting.db.cr.callback_data import ExecutionData, SBData
from contracting.db.driver import ContractDriver
from collections import deque
from typing import Callable
import traceback


class SubBlockClient:
    def __init__(self, sbb_idx, num_sbb, loop=None):
        name = self.__class__.__name__ + "[sbb-{}]".format(sbb_idx)
        self.log = get_logger(name)

        self.loop = loop or asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

        self.cache_manager = CacheManager(self.loop, sbb_idx, num_sbb)

    def execute_sb(self, input_hash: str, contracts: list, sub_block_idx: int,
                   completion_handler: Callable[[SBData], None], environment={}):
        if not self.cache_manager.is_cache_available():
            self.log.spam("No free cache available to execute input bag {}".format(input_hash))
            return False

        self.log.spam("Execute SB call for input hash {}".format(input_hash))
        bag = TransactionBag(contracts, input_hash, sub_block_idx, completion_handler)

        # Set the environment of the bag, which is going to be standard (time, blocknum, blockhash).
        bag.environment = environment

        self.cache_manager.execute_bag(bag)
        return True

    def update_master_db(self):
        self.cache_manager.update_master_db()

    def discord_current_sb(self):
        self.cache_manager.reset_current_db()

    def flush_all(self):
        self.cache_manager.flush_all()


POLL_INTERVAL = 0.1

class CacheManager:
    def __init__(self, loop, sbb_idx, num_sbb, executor=Executor(),
                 driver=ContractDriver(), num_caches=config.NUM_CACHES):
        self.loop = loop
        self.log = get_logger("Cache Manager")

        self.executor = executor
        self.master_db = driver

        # FIFO queues of caches
        self.free_caches = deque()
        self.working_caches = deque()
        self.recycling_caches = deque()

        # set up caches
        for i in range(num_caches):
            cache = CRCache(config.DB_OFFSET + i, self.master_db,
                            sbb_idx, num_sbb, self.executor)
            self.free_caches.append(cache)

        # Cilantro is in charge of starting the event loop. This coro will start as soon as cilantro
        # (SubBlockBuilder) kicks off his event loop
        self.fut = asyncio.ensure_future(self._poll_cache_events())

    def is_cache_available(self):
        return len(self.free_caches) > 0

    def _log_caches(self):
        self.log.spam("--------- WORKING CACHES ---------")
        for i, c in enumerate(self.working_caches):
            self.log.spam("idx {} --- {}".format(i, c))
        self.log.spam("----------------------------------")

        self.log.spam("--------- RECYCLING CACHES ---------")
        for i, c in enumerate(self.recycling_caches):
            self.log.spam("idx {} --- {}".format(i, c))
        self.log.spam("----------------------------------")

        self.log.spam("--------- FREE CACHES ---------")
        for i, c in enumerate(self.free_caches):
            self.log.spam("idx {} --- {}".format(i, c))
        self.log.spam("----------------------------------")


    def top_of_working_stack(self, cache: CRCache):
        if not self.working_caches:
            return False
        return self.working_caches[0] == cache

    def execute_bag(self, bag: TransactionBag):
        self.log.spam('Executing bag {}'.format(bag.transactions))
        current_cache = self.free_caches.popleft()
        current_cache.execute_bag(bag)

        self.working_caches.append(current_cache)
        # self._log_caches()

    def reset_current_db(self):
        cache = self.working_caches.popleft()
        cache.reset_dbs()
        self.recycling_caches.append(cache)

    def update_master_db(self):
        assert len(self.working_caches) > 0, "attempted to update master db but no working caches"
        # self._log_caches()

        self.working_caches[0].merge_to_master()
        self.reset_current_db()

    # shouldn't be flush all - only top of the stack that is not in reset state
    def flush_all(self):
        self.log.spam("Flushing all caches...")
        while len(self.working_caches) > 0:
            self.reset_current_db()

        # self._log_caches()

    async def _working_cache_event(self):
        if len(self.working_caches) == 0:
            return
        self.working_caches[0].cr_event()

    async def _recycling_cache_event(self):
        if len(self.recycling_caches) == 0:
            return
        if self.recycling_caches[0].is_reset():
            cache = self.recycling_caches.popleft()
            cache.mark_clean()
            self.free_caches.append(cache)

    async def _poll_cache_events(self):
        while True:
            await asyncio.sleep(POLL_INTERVAL)

            try:
                await self._working_cache_event()
                await self._recycling_cache_event()

            except Exception as e:
                self.log.fatal("Exception in the event manager: {}...\n".format(e))
                self.log.fatal(traceback.format_exc())

