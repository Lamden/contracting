import asyncio
import time
from contracting.logger import get_logger
from contracting.execution.executor import Executor
from contracting.db.cr.cache import CRCache
from contracting import config
from contracting.db.cr.transaction_bag import TransactionBag
from contracting.db.cr.callback_data import ExecutionData, SBData
from contracting.db.driver import ContractDriver
from collections import deque, defaultdict
from typing import Callable, List, Any
import traceback


class FSMScheduler:

    def __init__(self, loop, sbb_idx, num_sbb):
        self.log = get_logger("Poller")
        self.events = defaultdict(set)
        self.temp_events = defaultdict(set)
        self.loop = loop

        self.num_sbb = num_sbb
        self.sbb_idx = sbb_idx

        self.log.debug("Starting scheduler")

        # Cilantro is in charge of starting the event loop. This coro will start as soon as cilantro
        # (SubBlockBuilder) kicks off his event loop
        self.fut = asyncio.ensure_future(self._poll_events())

        self.available_caches = deque() # LIFO
        self.pending_caches = deque() # FIFO

        self.merge_idx = 0

    def execute_bag(self, bag: TransactionBag):
        assert len(self.available_caches) > 0, "No available caches"
        current_cache = self.available_caches.popleft()

        assert current_cache.state == 'CLEAN', "Pulled cache from available db with state {}, but expected CLEAN state"\
                                               .format(current_cache.state)

        current_cache.set_bag(bag)
        current_cache.execute()

        self.pending_caches.append(current_cache)

    def add_poll(self, cache: CRCache, func: callable, succ_state: str, is_merge=False):
        self.temp_events[cache].add((func, succ_state, is_merge))

    def mark_clean(self, cache: CRCache):
        if cache in self.pending_caches:
            self.pending_caches.remove(cache)
        self.available_caches.append(cache)

    def check_top_of_stack(self, cache: CRCache):
        return self.pending_caches[0] == cache

    def clear_polls_for_cache(self, cache: CRCache):
        if cache not in self.events:
            self.log.debug("Attempting to clear poll for cache {}, but no polls were registered".format(cache))
            return

        del self.events[cache]

    async def _poll_events(self):
        try:
            while True:
                self.log.spam("Polling events")

                rm_set = defaultdict(list)  # set of function pointer to remove if the poll call was successful

                for cache, poll_set in self.events.items():
                    for func, succ_state, is_merge in poll_set:

                        if not is_merge:
                            func()
                            if cache.state == succ_state:
                                self.log.debug("Polling function call {} resulting in succ state {}. Removing function from poll "
                                               "set.".format(func, succ_state))
                                rm_set[cache].append((func, succ_state, is_merge))

                        else:
                            try:
                                func()
                                if cache.state == succ_state:
                                    # TODO bump this guy down to debug or debugv once we feel confidence
                                    self.log.info("Polling function call {} resulting in succ state {}. Removing function from poll "
                                                   "set.".format(func, succ_state))
                                    rm_set[cache].append((func, succ_state, is_merge))
                                    self.merge_idx -= 1
                            except Exception as e:
                                # TODO bump this guy down to spam or debugv once we feel confidence
                                self.log.info("Got error try to call func {}...\nerr = {}".format(func, e))

                for cache, li in rm_set.items():
                    for tup in li:
                        self.events[cache].remove(tup)

                self.events.update(self.temp_events)
                self.temp_events.clear()

                await asyncio.sleep(config.POLL_INTERVAL)

        except Exception as e:
            self.log.fatal("big yikes in the _poll_events: {}...\nerror:".format(e))
            self.log.fatal(traceback.format_exc())
            raise e

    def update_master_db(self):
        assert len(self.pending_caches) > 0, "attempted to update master db but no pending caches"
        cache = self.pending_caches[self.merge_idx]
        self.merge_idx += 1
        self.add_poll(cache, cache.merge, 'RESET', True)

    def flush_all(self):
        self.log.info("Flushing all caches...")
        for cache in self.pending_caches:
            cache.discard()


class SubBlockClient:
    def __init__(self, sbb_idx, num_sbb, loop=None):
        name = self.__class__.__name__ + "[sbb-{}]".format(sbb_idx)
        self.log = get_logger(name)

        self.num_sbb = num_sbb
        self.sbb_idx = sbb_idx

        self.loop = loop or asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

        self.executor = Executor()
        self.master_db = ContractDriver()

        caches = []
        self.scheduler = FSMScheduler(self.loop, sbb_idx, num_sbb)
        for i in range(config.NUM_CACHES):
            caches.append(CRCache(config.DB_OFFSET + i, self.master_db,
                                  self.sbb_idx, self.num_sbb,
                                  self.executor, self.scheduler))

    def flush_all(self):
        self.scheduler.flush_all()

    def execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[SBData], None]):
        bag = TransactionBag(contracts, input_hash, completion_handler)
        self.scheduler.execute_bag(bag)

    def update_master_db(self):
        self.scheduler.update_master_db()
