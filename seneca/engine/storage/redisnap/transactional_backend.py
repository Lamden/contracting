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
    def __init__(self, transaction_group, tag):
        self._local_executer = l_back.Executer()
        self._dependencies = {}
        self._redo_ops = {}
        self._status = 'in-progress'
        self.tag = tag
        self._transaction_group = transaction_group # Needed

    def set_status(self, status):
        assert status in ['in-progress', 'done', 'dirty'], 'Invalid status: ' + str(status)
        self._status = status

    def get_status(self):
        return self._status

    def _get_upstream(self):
        return self._transaction_group._get_upstream_executer(self)

    def __call__(self, cmd):
        if isinstance(cmd, Write) or isinstance(cmd, Mutate):
            # TODO: don't replace, merge
            self._redo_ops[cmd.key] = cmd
        elif isinstance(cmd, Read) or isinstance(cmd, TypeCheck):
            # TODO: don't replace, merge
            self._dependencies[cmd.key] = cmd

        return self.run_only_no_logs(cmd)

    def run_only_no_logs(self, cmd):
        res = self._local_executer(cmd)
        if isinstance(res, RDoesNotExist):
            return self._get_upstream().run_only_no_logs(cmd)
        else:
            return res


class RedisBackendWapper:
    """
    Wrapper adds un_only_no_logs to Redis backend object.
    """
    def __init__(self, *args, **kwargs):
        self.wrapped = r_back.Executer(*args, **kwargs)

    def __call__(self, cmd):
        return self.wrapped(cmd)

    def run_only_no_logs(self, cmd):
        return self(cmd)

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr)


class TransactionGroup:
    def __init__(self, *args, **kwargs):
        self._redis_backend = RedisBackendWapper(*args, **kwargs)
        self._active_transaction = None
        self._transactions = []
        self._transactions_by_tag = {}

    def finalize_current_transaction(self):
        #check contracts after current for dependecies
        #set current as done
        #self._active_transaction = None
        # What else?
        raise NotImplementedError()

    def _get_active_transaction_index(self):
        # TODO: make this look nicer
        return list(filter(lambda i_x: i_x[1] == self._active_transaction, enumerate(self._transactions)))[0][0]

    def _get_upstream_executer(self, ex):
        i = self._get_active_transaction_index()
        if i == 0:
            return self._redis_backend
        else:
            return self._transactions[i - 1]


    def start_new_transaction(self, tag, index=None):
        """
        Specify an index to start writing
        """
        index = index if index else len(self._transactions)

        assert index <= len(self._transactions)
        assert tag not in self._transactions_by_tag, 'Tags must be unique.'
        # TODO: assert no bad transactions before this one

        s = Transaction(self, tag)
        self._transactions.insert(index, s)

        self._active_transaction = s
        self._transactions_by_tag[s.tag] = s

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

        return cmd.safe_run(self._active_transaction)




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
    "'NoneType' object has no attribute 'run_only_no_logs'"

    # Set key in transaction 'testing-trans-1'
    >>> ex(Set('foo', 'bar'))

    >>> ex._active_transaction._local_executer(Get('foo'))
    RScalar('bar')

    ### Add Redis backend to TransactionGroup for more tests ###
    >>> ex._redis_backend = rbe

    # Read falls through to Redis
    >>> ex(Get('baz'))
    RDoesNotExist()

    # Add a second transaction on stack

    # Same tag value, will fail.
    >>> exception_to_string(ex.start_new_transaction, 'testing-trans-1')
    'Tags must be unique.'

    >>> ex.start_new_transaction('testing-trans-2')

    # Foo not in active
    >> ex._active_transaction._local_executer(Get('foo'))
    RDoesNotExist()

    # Foo not in Redis
    >>> ex._redis_backend(Get('foo'))
    RDoesNotExist()

    # Foo comes from testing-trans-1
    >>> ex(Get('foo'))
    RScalar('bar')

    # Overwrite foo in testing-trans-2
    >> ex(Set('foo', 'baz')); ex(Get('foo'))
    RScalar('baz')
    >>> ex._transactions[0](Get('foo'))
    RScalar('bar')

    '''

    import doctest, sys

    def exception_to_string(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return str(e)

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
