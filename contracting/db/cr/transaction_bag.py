from contracting.logger import get_logger
from typing import Callable

log = get_logger('Contracting[TX-Bag]')

class TransactionBag:
    def __init__(self, transactions: list, input_hash: str, sub_block_idx: int,
                       completion_handler: Callable, environment={}):
        self.input_hash = input_hash
        self.transactions = transactions
        self.to_yield = list(range(len(self.transactions)))
        self.sub_block_idx = sub_block_idx
        self.completion_handler = completion_handler
        self.environment = environment

    def __iter__(self):
        for i in self.to_yield:
            yield i, self.transactions[i]

    def yield_from(self, idx):
        """
        Update the list of indicies to yield from a new start point

        :param idx: index to begin the yield from
        :return:
        """
        if idx > 0:
            self.to_yield = list(range(idx, len(self.transactions)))

    def get_tx_at_idx(self, idx):
        return self.transactions[idx]
