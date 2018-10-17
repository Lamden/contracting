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
    def __init__(self, contract_str: str, sender_id: str, sbb_idx: int, order_idx: int):
        self.contract_str, self.sender_id, self.sbb_index, self.order_number = contract_str, sender_id, sbb_idx, order_idx


class SenecaClient:

    def __init__(self, loop=None, name=None, get_log_fn=None):
        name = name or self.__class__.__name__
        get_log_fn = get_log_fn or SenecaLogger
        self.log = get_log_fn(name)
        self.queue = deque()

    def finalize(self):
        self.log.notice("Finalizing transactions...")
        pass
