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
from seneca.engine.util import auto_set_fields
from abc import ABCMeta, abstractmethod
from seneca.engine.storage.redisnap.backend_abc import ExecuterBase as abc_executer


class NoTransactionsInGroup(Exception):
    pass


class OpTracker(ReprIsConstructor):
    """
    >>> o = OpTracker()
    >>> print(o)
    OpTracker({})

    >>> o.add(Get('foo')); print(o)
    OpTracker({'foo': [Get('foo')]})
    """
    # TODO: implement for hash field addrs as well
    def __init__(self):
        self.data = {}

    def add(self, cmd):
        if hasattr(cmd, 'field'):
            raise NotImplementedError()

        if cmd.key not in self.data:
            self.data[cmd.key] = []

        self.data[cmd.key].append(cmd)

    # TODO: This function has to both implement fields and get a lot smarter.
    def contains_command_addr(self, cmd):
        if hasattr(cmd, 'field'):
            raise NotImplementedError()

        return cmd.key in self.data

    def __repr__(self):
        return 'OpTracker(%s)' % str(self.data)


class Transaction:
    """
    >>> t = Transaction(None, 'testing')
    >>> print(t)
    Transaction({'_local_executer': ExecuterBase({}), '_read_deps': OpTracker({}), '_typecheck_deps': OpTracker({}), '_redo_log': OpTracker({}), '_mutation_tracker': OpTracker({}), '_status': 'open', 'tag': 'testing', '_transaction_group': None})
    """
    def __init__(self, transaction_group, tag):
        #self._local_executer = TransactionalExecuter()
        self._local_executer = l_back.Executer()

        self._read_deps = OpTracker()
        self._typecheck_deps = OpTracker()
        self._redo_log = OpTracker()
        self._mutation_tracker = OpTracker()

        self._status = 'open'
        self.tag = tag
        self._transaction_group = transaction_group # Needed

    def __repr__(self):
        return 'Transaction(%s)' % str(self.__dict__)

    def set_status(self, status):
        assert status in ['open', 'closed', 'dirty'], 'Invalid status: ' + str(status)
        self._status = status

    def get_status(self):
        return self._status

    def _get_upstream(self):
        return self._transaction_group._get_upstream_executer(self)

    def appendwo(self, cmd):
        current = self.recursive_upstream_call(Get(cmd.key))

        if isinstance(current, RDoesNotExist):
            self._local_executer(cmd)
        else:
            self._local_executer(Set(cmd.key, current + cmd.value))

    def run_mutate_command(self, cmd):
        cmd_type = type(cmd)

        if cmd_type == AppendNR:
            return self.appendwo(cmd)
        else:
            raise NotImplementedError()

    def __call__(self, cmd):
        if isinstance(cmd, Write):
            '''
            Writes are the simplest case: add them to the redo_log, run locally
            '''
            self._redo_log.add(cmd)
            self._local_executer(cmd)


        elif isinstance(cmd, Mutate):
            '''
            If the data is already present locally, it can simply be edited.
            If not, we need to recurse to get the data to be mutated, then write
            locally, and also track the mutation so if there are any subsequent
            reads, they get registered as external reads.
            '''
            self._redo_log.add(cmd)

            if self._local_executer.contains_command_addr(cmd):
                self._local_executer(cmd)
            else:
                self._mutation_tracker.add(cmd)
                self.run_mutate_command(cmd)


        if isinstance(cmd, TypeCheck):
            '''
            Typechecks are also simple. The really difficult stuff is a result
            of lazily evaluated mutating operations, typechecks don't care about
            those because they don't change the type.
            '''
            if self._local_executer.contains_command_addr(cmd):
                return self._local_executer(cmd)
            else:
                self._typecheck_deps.add(cmd)
                return self.recursive_upstream_call(cmd)


        elif isinstance(cmd, Read):
            '''
            Reads recurse if data not present locally, lack of local data
            triggers creation of a read dependency. Also, data that's read and
            has been regiestered in the mutation tracker also triggers a read
            dependency.
            '''
            if not self._local_executer.contains_command_addr(cmd):
                self._read_deps.add(cmd)
                return self.recursive_upstream_call(cmd)
            else:
                if self._mutation_tracker.contains_command_addr(cmd):
                    self._read_deps.add(cmd)

                return self._local_executer(cmd)


    def recursive_upstream_call(self, cmd):
        # Note: There should never be and dependency/redo logging in the method.
        if self._local_executer.contains_command_addr(cmd):
            return self._local_executer(cmd)
        else:
            return self._get_upstream().recursive_upstream_call(cmd)



class RedisBackendWapper:
    def __init__(self, *args, **kwargs):
        self.wrapped = r_back.Executer(*args, **kwargs)

    def __call__(self, cmd):
        return self.wrapped(cmd)

    def recursive_upstream_call(self, cmd):
        return self(cmd)

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr)


class TransactionGroup(abc_executer):
    def __init__(self, *args, **kwargs):
        self._redis_backend = RedisBackendWapper(*args, **kwargs)
        self._active_transaction = None
        self._transactions = []
        self._transactions_by_tag = {}

    def finalize_current_transaction(self):
        if self._get_transaction_index(self._active_transaction) == len(self._transactions) - 1:
            self._active_transaction.set_status('closed')
            self._active_transaction = None
        else:
            raise NotImplementedError()

    def _get_transaction_index(self, ex):
        return list(filter(lambda i_x: i_x[1] == ex, enumerate(self._transactions)))[0][0]

    def _get_upstream_executer(self, ex):
        i = self._get_transaction_index(ex)
        if i > 0:
            return self._transactions[i - 1]
        else:
            return self._redis_backend


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

    def get_pending_ops(self):
        ret = []
        for t in self._transactions:
            for cmd_list in t._redo_log.data.values():
                for c in cmd_list:
                    ret.append(c)

        return ret

    def commit_all_to_redis(self):
        for c in self.get_pending_ops():
            self._redis_backend(c)
        self._transactions = []


    def clear(self):
        raise NotImplementedError()

    def __call__(self, cmd):
        # Dissallow writes directly to Redis, reads and typechecks are okay.
        if not self._transactions:
            raise NoTransactionsInGroup('You must create a transaction before executing write commands.')

        return cmd.safe_run(self._active_transaction)


def run_tests(deps_provider):
    '''
    >>> ex1 = TransactionGroup(host='127.0.0.1', port=32768)
    >>> ex._redis_backend.purge()

    # Operations should fail before transaction has been created.
    >>> exception_type_name(ex, Get('foo'))
    'NoTransactionsInGroup'

    >>> ex.start_new_transaction('testing-trans-1')

    >>> ex(AppendNR('foo', 'bar'))
    >>> ex._active_transaction._read_deps.contains_command_addr(Get('foo'))
    False
    >>> ex._active_transaction._mutation_tracker.contains_command_addr(Get('foo'))
    True

    >>> ex(Get('foo'))
    RScalar('bar')
    >>> ex._active_transaction._read_deps.contains_command_addr(Get('foo'))
    True
    >>> ex._active_transaction._mutation_tracker.contains_command_addr(Get('foo'))
    True

    >>> ex(Del('foo'))
    >>> ex(Get('foo'))
    RDoesNotExist()


    ### Run the following test without a Redis backend ###
    >>> rbe = ex._redis_backend
    >>> ex._redis_backend = None


    # Test tries to fall through to Redis, but it has been removed
    >>> exception_type_name(ex, Get('baz'))
    'AttributeError'


    # Set key in transaction 'testing-trans-1'
    >>> ex(SetNR('foo', 'bar'))

    >>> ex._active_transaction._local_executer(Get('foo'))
    RScalar('bar')

    ### Add Redis backend to TransactionGroup for more tests ###
    >>> ex._redis_backend = rbe

    # Read falls through to Redis
    >>> ex(Get('baz'))
    RDoesNotExist()

    >>> ex.start_new_transaction('testing-trans-2')
    >>> ex._active_transaction.tag
    'testing-trans-2'

    >>> ex._get_upstream_executer(ex._active_transaction) != ex._active_transaction
    True

    >>> t1 = ex._get_upstream_executer(ex._active_transaction)
    >>> t1.tag
    'testing-trans-1'

    >>> type(ex._get_upstream_executer(t1)).__name__
    'RedisBackendWapper'

    >>> ex(Get('baz'))
    RDoesNotExist()

    # Same tag value, will fail.
    >>> exception_type_name(ex.start_new_transaction, 'testing-trans-1')
    'AssertionError'

    >>> ex.start_new_transaction('testing-trans-3')

    # Foo not in active
    >>> ex._active_transaction._local_executer(Get('foo'))
    RDoesNotExist()

    # Foo not in Redis
    >>> ex._redis_backend(Get('foo'))
    RDoesNotExist()

    # Foo comes from testing-trans-1
    >>> ex(Get('foo'))
    RScalar('bar')

    # Overwrite foo in testing-trans-2
    >>> ex(SetNR('foo', 'baz')); ex(Get('foo'))
    RScalar('baz')
    >>> ex._transactions[0](Get('foo'))
    RScalar('bar')

    >>> ex(AppendNR('foo', 'bar'))
    >>> ex(Get('foo'))
    RScalar('bazbar')

    >>> ex._active_transaction._mutation_tracker.contains_command_addr(Get('foo'))
    False
    >>> ex(Get('new_key_doesnt_exist'))
    RDoesNotExist()

    ### Test commit ordering ###
    >>> ex2 = TransactionGroup(host='127.0.0.1', port=32768)
    >>> ex2._redis_backend.purge()
    >>> ex2.start_new_transaction('a')
    >>> ex2(SetNR('foo', 'a'))
    >>> ex2(SetNR('foo', 'b'))
    >>> ex2(SetNR('foo', 'c'))
    >>> ex2(SetNR('foo', 'd'))
    >>> ex2.start_new_transaction('b')
    >>> ex2(SetNR('foo', 'e'))
    >>> ex2(SetNR('foo', 'f'))
    >>> ex2(SetNR('foo', 'g'))
    >>> ex2(SetNR('foo', 'h'))
    >>> _ = [print(x) for x in ex2.get_pending_ops()]
    SetNR('foo', 'a')
    SetNR('foo', 'b')
    SetNR('foo', 'c')
    SetNR('foo', 'd')
    SetNR('foo', 'e')
    SetNR('foo', 'f')
    SetNR('foo', 'g')
    SetNR('foo', 'h')
    >>> ex.commit_all_to_redis()
    '''

    import doctest, sys

    ex = TransactionGroup(host='127.0.0.1', port=32768)
    from seneca.engine.util import return_exception_tuple

    def exception_type_name(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return type(e).__name__


    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
