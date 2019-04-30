import asyncio
import time
from seneca.logger import get_logger
from seneca.execution.executor import Executor
from seneca.db.cr.cache import CRCache
from seneca import config
from seneca.db.cr.transaction_bag import TransactionBag
from seneca.db.driver import ContractDriver
from collections import deque, defaultdict
from typing import Callable, List
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


    def execute_bag(self, bag: TransactionBag):
        assert len(self.available_caches) > 0, "No available caches"
        current_cache = self.available_caches.popleft()

        assert current_cache.state == 'CLEAN', "Pulled cache from available db with state {}, but expected CLEAN state"\
                                               .format(current_cache.state)

        current_cache.set_bag(bag)
        current_cache.execute()

        self.pending_caches.append(current_cache)

    def add_poll(self, cache: CRCache, func: callable, succ_state: str):
        self.temp_events[cache].add((func, succ_state))

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
            self.log.critical("starting poller for events")  # todo delete
            while True:
                # self.log.debugv("Polling events")
                self.log.important3("Polling events")

                rm_set = defaultdict(list)  # set of function pointer to remove if the poll call was successful

                for cache, poll_set in self.events.items():
                    for func, succ_state in poll_set:

                        # debug
                        self.log.important("polling func {} on cache {}".format(func, cache))
                        # end debug

                        # Execute the func to poll the FSM, and check if that resulted in the desired state change.
                        # If so, remove this event from Poller
                        # TODO how to add the next event to the Poller tho?
                        func()
                        if cache.state == succ_state:
                            self.log.debug("Polling function call {} resulting in succ state {}. Removing function from poll "
                                           "set.".format(func, succ_state))
                            rm_set[cache].append((func, succ_state))

                for cache, li in rm_set.items():
                    for tup in li:
                        self.events[cache].remove(tup)

                self.log.notice("sleeping {} before next poll".format(config.POLL_INTERVAL))

                self.events.update(self.temp_events)
                self.temp_events.clear()

                await asyncio.sleep(config.POLL_INTERVAL)
                self.log.notice("done with slep")

        except Exception as e:
            self.log.fatal("type of error: {}".format(type(e)))
            self.log.fatal("big yikes: {}".format(e))
            self.log.info(traceback.format_exc())

    def update_master_db(self):
        assert len(self.pending_caches) > 0, "attempted to update master db but no pending caches"
        cache = self.pending_caches[0]
        cache.merge()


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
        self.scheduler = FSMScheduler(self.loop, sbb_idx, num_sbb, caches)
        for i in config.NUM_CACHES:
            caches.append(CRCache(config.DB_OFFSET + i, self.master_db,
                                  self.sbb_idx, self.num_sbb,
                                  self.executor, self.scheduler))

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

    def execute_sb(self, input_hash: str, contracts: list, completion_handler: Callable[[List[tuple]], None]):
        bag = TransactionBag(contracts, input_hash, completion_handler)
        self.scheduler.execute_bag(bag)

    def update_master_db(self):
        self.scheduler.update_master_db()

    ######################
    ## INTERNAL METHODS ##
    ######################
