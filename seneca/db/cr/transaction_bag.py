from seneca.db.cr.conflict_resolution import CRContext
from typing import List


class TransactionBag:
    def __init__(self, transactions: List[tuple], cr_context: CRContext):
        self.cr_context = cr_context
        self.transactions = sorted(transactions, key=lambda x: x[0])

    def __iter__(self):
        for t in self.transactions:
            yield t



