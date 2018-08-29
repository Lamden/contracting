"""
This module is the core logic of Redisnap, transactions/snapshots/savepoints are
implemented here.

It provides a superset of the the other backend APIs, adding methods to control
creation of new transactions, commits, and rollbacks.
"""
import redis as rr
from seneca.engine.storage.redisnap.commands import *

class Transaction:
    def __init__(self, transaction_group):
        self._pending_changes = {} # dict of keys, figure out how this words with mset
        self._transaction_group = transaction_group6
        self._is_soft_commited = False
        self._revision = 0
        self._write_only_revision = 0

    def soft_commit(self):
        if self._transaction_group:
            # get downstream committed transactions (if there are any)
            # check for read dependencies in those transactions against writes in this one.
            raise NotImplementedError()
            # self._is_soft_commited = True

        self._is_soft_commited = True
        return True

    def get_soft_committed(self):
        return self._is_soft_commited

    def clear(self):
        if self._transaction_group:
            raise NotImplementedError()

        self._pending_changes = {}


class TransactionGroup:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()
        self.executer = rr.StrictRedis(*args, **kwargs)
        self.save_points = []

    def append_new_transaction(self):
        return self.insert_new_transaction(len(self.save_points))

    def insert_new_transaction(self, index):
        sp = SavePoint(self)
        self.save_points.index(indesx, sp)
        return sp

    def get_upstream(self, transaction):
        raise NotImplementedError()

    def get_upstream(self, transaction):
        raise NotImplementedError()

    def write_out(self):
        # TODO: optimize by compacting transactions before sending
        # TODO: commit to Redis
        raise NotImplementedError()


def run_tests(deps_provider):
    '''
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
