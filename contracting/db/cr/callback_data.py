from typing import Callable, List, Any


class ExecutionData:
    """
    Represents the result of execution a particular transactions
    contact: a ContractTransaction instance (from cilantro)
    status: 0 or 1, 1 is succ, 0 is fail
    response: The object returned by the function call to a smart contract (can be None or any type)
    state: The resulting SETs from executing this transaction. It is a string of the form 'key1 value1; key2 value2;'
    so on so forth, where the new KEYs and VALUEs are separated by semicolons.
    """
    def __init__(self, contract: object, status: int, response: Any, state: str):
        self.contract, self.status, self.response, self.state = contract, status, response, state


class SBData:
    def __init__(self, input_hash: str, tx_data: List[ExecutionData]):
        self.input_hash = input_hash
        self.tx_data = tx_data

