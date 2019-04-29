from ...logger import get_logger
from typing import Callable

from transitions import Machine


class TransactionBag:
    def __init__(self, transactions: list, input_hash: str, completion_handler: Callable):
        self.input_hash = input_hash
        self.transactions = transactions
        self.to_yield = list(range(len(self.transactions)))
        self.completion_handler = completion_handler

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
