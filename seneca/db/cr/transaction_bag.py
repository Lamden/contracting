from seneca.db.cr.conflict_resolution import CRContext
from typing import List


class TransactionBag:
    def __init__(self, transactions: List[tuple], cr_context: CRContext):
        self.cr_context = cr_context
        self.transactions = sorted(transactions, key=lambda x: x[0])

    def __iter__(self):
        for t in self.transactions:
            yield t

    # ideally we should have designed the bag to do this in O(1) but w/e yolo imma just b search that shit
    def get_tx_at_idx(self, idx: int):
        i, j = 0, len(self.transactions) - 1

        while j >= i:
            mid = (i+j) // 2
            if self.transactions[mid][0] == idx:
                return self.transactions[mid][1]
            elif self.transactions[mid][0] > idx:
                j = mid-1
            else:
                i = mid+1

        raise Exception("No transaction found in bag with index {}! Bag's transactions: {}"
                        .format(idx, self.transactions))




