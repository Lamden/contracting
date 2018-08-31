"""
This module is the core logic of Redisnap, transactions/snapshots/savepoints are
implemented here.

It provides a superset of the the other backend APIs, adding methods to control
creation of new transactions, commits, and rollbacks.
"""
import redis as rr
from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.local_backend as l_back
import seneca.engine.storage.redisnap.redis_backend as r_back
from collections import OrderedDict

class KeyNotFoundTryOlder(Exception):
    pass

class Transaction:
    def __init__(self, transaction_group, tag):
        self._local_executer = l_back.Executer()
        self._dependencies = set()
        self._status = 'in-progress'
        self.tag = tag
        self._transaction_group = transaction_group # Needed?

    def set_status(self, status):
        assert status in ['in-progress', 'done', 'dirty'], 'Invalid status: ' + str(status)
        self._status = status

    def get_status(self):
        return self._status

    def __call__(self, cmd):
        """
        * If read or type_dep, add to

        """
        raise NotImplementedError()



class TransactionGroup:
    def __init__(self, *args, **kwargs):
        self._redis_backend = r_back.Executer(*args, **kwargs)
        self._active_transaction = None
        self._transactions = []
        self._transaction_tags = set()

    def finalize_current_transaction(self):
        #check contracts after current for dependecies
        #set current as done
        #self._active_transaction = None
        # What else?
        raise NotImplementedError()

    def start_new_transaction(self, tag, index=None):
        """
        Specify an index to start writing
        """
        assert index <= len(self.save_points)
        assert tag not in self._save_point_tags, 'Tags must be unique.'
        # TODO: assert no bad transactions before this one

        index = index if index else len(self.save_points)
        s = SavePoint(tag)
        self._save_points.insert(index, s)

        self._active_save_point = s
        self._save_point_tags.add(s.tag)

    def start_new_transaction_before_tag(self, this_tag, other_tag):
        # find this_tag index
        # start_new_transaction(self, tag, index=None)
        raise NotImplementedError()

    def rework_transaction(self, tag):
        raise NotImplementedError()

    def commit_all_to_redis(self):
        raise NotImplementedError()

    def clear(self):
        self.__init__()

    def __call__(self, cmd):
        raise NotImplementedError()


def run_tests(deps_provider):
    '''
    >>> ex = TransactionGroup(host='127.0.0.1', port=32768)

    '''

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
