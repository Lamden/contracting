# from collections import deque
# from heapq import heappush, heappop
# from typing import List
# import time
# import asyncio
# from seneca.logger import SenecaLogger
# from seneca.engine.executor import SenecaExecutor
#
# # this is the seneca interpreter that sub-block builders will use it.
# # it should be pretty similar to current SenecaExecutor
# #    - will execute the txns locally and maintains a list of txns, with status, state, etc. see interpreter.py
# #    - it will also have a higher level apis to orchestrate sub-block contenders
#
# class ContractStruct:
#     """
#     This class acts as a simple data structure for holding all information necessary to execute smart contracts using
#     the SenecaClient. ContractStructs should be created inside Cilantro, and passed into the SenecaClient for execution
#     """
#     def __init__(self, contract_str: str, sender_id: str, order_idx: int):
#         self.contract_str, self.sender_id, self.order_number = contract_str, sender_id, order_idx
#
#
# class SenecaClient:
#
#     def __init__(self, sbb_idx:int, loop=None, name=None, get_log_fn=None):
#         name = name or self.__class__.__name__
#         get_log_fn = get_log_fn or SenecaLogger
#         self.log = get_log_fn(name)
#         # self.sbb_idx = sbb_idx
#         self.executor = SenecaExecutor(sbb_idx)
#
#     def finalize(self):
#         # do we need this method? what's finalizing transactions? Davis?
#         self.log.notice("Finalizing transactions...")
#         pass
#
#
#     def catchup(self):
#         pass
#
#
#     def flush(self, update_state=True):
#         """
#         Flushes internal queue of transactions. If update_state is True, this will also commit the changes
#         to the database. Otherwise, this method will discard any changes
#         """
#         self.executor.flush(update_state=update_state)
#
#     def run_contract(self, contract):
#         # raghu todo need to update this to ContractStruct or something
#         assert isinstance(contract, OrderingContainer), \
#             "Seneca Interpreter can only interpret OrderingContainer instances"
#
#         self.executor.run_contract(contract)
#
#     # calling function has to check status and if it is false, it has to wait or come back to execute it again
#     def start_sub_block(self):
#         return self.executor._start_next_sb()
#
#     def end_sub_block(self):
#         self.executor._end_sb()
#
#     def get_next_sub_block(self):
#         return self.executor._make_next_sb()
#
#     # do we need these methods in our new flow? Davis?
#     def start(self):
#         assert self.check_contract_future is None, "Start should not be called twice without a .stop() in between!"
#
#         # Check to see if there are valid contracts to be run
#         self.check_contract_future = asyncio.ensure_future(self.check_contract())
#
#     def stop(self):
#         self.check_contract_future.cancel()
#         self.check_contract_future = None
