from collections import deque
from heapq import heappush, heappop
from typing import List
import time
import asyncio
from seneca.logger import SenecaLogger

# this is the seneca interpreter that sub-block builders will use it.
# it should be pretty similar to current SenecaInterpreter
#    - will execute the txns locally and maintains a list of txns, with status, state, etc. see interpreter.py
#    - it will also have a higher level apis to orchestrate sub-block contenders

class ContractStruct:
    """
    This class acts as a simple data structure for holding all information necessary to execute smart contracts using
    the SenecaClient. ContractStructs should be created inside Cilantro, and passed into the SenecaClient for execution
    """
    def __init__(self, contract_str: str, sender_id: str, order_idx: int):
        self.contract_str, self.sender_id, self.order_number = contract_str, sender_id, order_idx




class SenecaClient:

    def __init__(self, loop=None, name=None, get_log_fn=None, sb_idx: int):
        name = name or self.__class__.__name__
        get_log_fn = get_log_fn or SenecaLogger
        self.log = get_log_fn(name)
        # self.sb_idx = sb_idx
        self.interpreter = SenecaInterpreter(sb_idx)
        self.queue = deque()

    def finalize(self):
        self.log.notice("Finalizing transactions...")
        pass


    def catchup(self):
        pass


    def flush(self, update_state=True):
        """
        Flushes internal queue of transactions. If update_state is True, this will also commit the changes
        to the database. Otherwise, this method will discard any changes
        """
        self.interpreter.flush(update_state=update_state)
        self.queue.clear()

    def run_contract(self, contract):
        # raghu todo need to update this to ContractStruct or something
        assert isinstance(contract, OrderingContainer), \
            "Seneca Interpreter can only interpret OrderingContainer instances"

        txn = self.interpreter.run_contract(contract)
        self.quue.append(txn)

    def get_tx_queue(self) -> List[TransactionData]:
        return list(self.queue)

    @property
    def queue_size(self):
        return len(self.queue)

    def start(self):
        assert self.check_contract_future is None, "Start should not be called twice without a .stop() in between!"

        # Check to see if there are valid contracts to be run
        self.check_contract_future = asyncio.ensure_future(self.check_contract())

    def stop(self):
        self.check_contract_future.cancel()
        self.check_contract_future = None
