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

class KeyNotFoundTryAncestor(Exception):
    pass

class NoTransactionsInGroup(Exception):
    pass

class Transaction:
    def __init__(self, tag):
        self._local_executer = l_back.Executer()
        self._dependencies = set()
        self._status = 'in-progress'
        self.tag = tag
        #self._transaction_group = transaction_group # Needed

    def set_status(self, status):
        assert status in ['in-progress', 'done', 'dirty'], 'Invalid status: ' + str(status)
        self._status = status

    def get_status(self):
        return self._status

    def __call__(self, cmd):
        """
        * If read or type_dep, add to

        """
        res = self._local_executer(cmd)
        if isinstance(res, RDoesNotExist):
            raise KeyNotFoundTryAncestor()
        else:
            return res



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
        index = index if index else len(self._transactions)

        assert index <= len(self._transactions)
        assert tag not in self._transaction_tags, 'Tags must be unique.'
        # TODO: assert no bad transactions before this one

        s = Transaction(tag)
        self._transactions.insert(index, s)

        self._active_transaction_index = index
        self._active_transaction = s
        self._transaction_tags.add(s.tag)

    def start_new_transaction_before_tag(self, this_tag, other_tag):
        # find this_tag index
        # start_new_transaction(self, tag, index=None)
        raise NotImplementedError()

    def rework_transaction(self, tag):
        raise NotImplementedError()

    def commit_all_to_redis(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def __call__(self, cmd):
        # Dissallow writes directly to Redis, reads and typechecks are okay.
        if not self._transactions:
            if isinstance(cmd, Write):
                raise NoTransactionsInGroup('You must create a transaction before executing write commands.')
            else:
                return self._redis_backend(cmd)

        i = self._active_transaction_index
        while i >= 0:
            try:
                return self._transactions[i](cmd)
            except KeyNotFoundTryAncestor:
                pass
            i -= 1

        return self._redis_backend(cmd)


def run_tests(deps_provider):
    '''
    >>> ex = TransactionGroup(host='127.0.0.1', port=32768)
    >>> ex._redis_backend.purge()

    # Test readonly direct redis access before transaction has been created.
    >>> ex(Get('foo'))
    RDoesNotExist()

    # Test write to direct redis access fails before transaction has been created.
    >>> exception_to_string(ex, Set('foo', 'bar'))
    'You must create a transaction before executing write commands.'


    ### Run the following test without a Redis backend ###
    >>> rbe = ex._redis_backend
    >>> ex._redis_backend = None

    # Create transaction
    >>> ex.start_new_transaction('testing-trans-1')

    # Test tries to fall through to Redis, but it has been removed
    >>> exception_to_string(ex, Get('baz'))
    "'NoneType' object is not callable"

    # Set key in transaction 'testing-trans-1'
    >>> ex(Set('foo', 'bar'))

    >>> ex._active_transaction._local_executer(Get('foo'))
    RScalar('bar')

    ### Add Redis backend to TransactionGroup for more tests ###
    >>> ex._redis_backend = rbe

    # Read falls through to Redis
    >>> exception_to_string(ex, Get('baz'))
    RDoesNotExist()







    '''

    import doctest, sys

    def exception_to_string(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return str(e)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
