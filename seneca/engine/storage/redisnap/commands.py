"""
This module contains types that describe Redis commands, but the commands don't
have an implementation, e.g. Get doesn't have a method like:
> Set('foo', 'bar').to_redis_string()
SET foo bar

This is important as these commands get run in completely different ways if they
are run against local memory, a remote Redis instance, or the transactional
backend.

Furthermore, these commands are not made to be subtyped for specific
implementations. This has been done for two reasons:

* Transactional backend is the primary use of this module, that backend wraps
local and redis backends, and commands may be attempted locally and ultimately
run remotely. In that scenario, a command would have to be awkwardly upcast to
a more general type, then downcast to the Redis backend subtype.

* All commands have a safe_run() method. This function runs one or more Redis
commands along with Python logic. The purpose of safe_run is to ensure that in
the context of a transaction, if a command is approved for a local write, it
won't fail when the transaction is committed and the command runs again against
the Redis backend. In these methods the command would have to pick the correct
implemenation for all other commands it runs based on its subtype. This would
also be awkward.

* NOTE: As a convention, command objects take regular Python types in their
constructors (not wrapped/RTypes like RScalarInt). The executers that run them
will generate RTypes for writing to db, and for returning local store and for
return values.

TODO: Switch from key input type to strings that more closely match RESP
TODO: Switch all "WO" - write-only commands to "NR" - no-read
"""
from abc import ABCMeta, abstractmethod
from typing import Union, List

from seneca.engine.util import auto_set_fields
from seneca.engine.storage.redisnap.resp_types import *

# TODO: Enforce run return types for run method in executer libs.


class Command(ReprIsConstructor):
    def run(self, ex):
        '''
        Execute the command. Passing an executer like this allows the command
        objects to exist completely separate from an executer. We'll implement
        at least two executers, direct Redis and nested snapshots, a.k.a.
        transactions with savepoints.

        It may seem oddly inside-out: obj.run(ex) -> ex(obj). It's done like
        this to enforce correct return type from executers that handle these
        commands.
        '''
        return ex(self)

    @abstractmethod
    def safe_run(self, local_ex):
        pass


# Inheriting these classes designates the subtype as performing these general
# types of operation on Redis.
class TypeCheck(Command): pass
class Read(Command): pass

class Write(Command):
    # def to_data_dependency(self):
    #     return None
    pass

class Mutate(Command):
    """
    Mutates alter data like writes, but unlike writes, if the mutated value
    is read, it will create a read dependancy on previous contracts, this
    is not the case with regular writes.
    """
    pass


#NOTE: This is a decorator function, not a class!
class run_methods_return_type:
    """
    TODO: This thing totally doesn't work. The annotation affect all classes in
    the hierarchy. Fix it.

    Ideally it should decorate both run()( and safe_run()
    """
    @auto_set_fields
    def __init__(self, t):
        pass

    def __call__(self, cls):
        cls.run.__annotations__['return'] = self.t
        return cls


def run_method_is_safe(cls):
    """
    This class decorator function designates that the the class it's run on
    has a safe run method i.e. it will never fail due to uncertain data on a
    Redis server. It actually sets the safe_run() method to run the code in the
    run() method.
    """
    # TODO: abstract this functionality and move to util
    if hasattr(cls, '__abstractmethods__'):
        abstr_methods = set(cls.__abstractmethods__)
        abstr_methods.remove('safe_run')
        cls.__abstractmethods__ = frozenset(abstr_methods)
    setattr(cls, 'safe_run', cls.run)
    return cls

################
# Key Commands #
################
@run_methods_return_type(type)
@run_method_is_safe
class Type(Command):
    """
    This is the built-in shallow Redis typecheck.

    >>> _ = ex.purge()
    >>> t = ex(Type('foo'))
    >>> print(t.__name__)
    RDoesNotExist
    >>> issubclass(t, RScalar)
    True
    """
    @auto_set_fields
    def __init__(self, key):
        pass


@run_methods_return_type(bool)
@run_method_is_safe
class Exists(Command):
    """
    >>> _ = ex.purge()
    >>> ex(Exists('foo'));
    False
    """
    @auto_set_fields
    def __init__(self, key):
        pass

    # to_data_dependency(self):
    #     return ExistentialDependancy(self.key)

@run_methods_return_type(type(None))
@run_method_is_safe
class Del(Write):
    @auto_set_fields
    def __init__(self, key):
        pass

    # to_data_dependency(self):
    #     return None

'''
Not yet implmented:
DUMP, EXPIRE, EXPIREAT, MIGRATE, MOVE, OBJECT, PERSIST, PEXPIRE, PEXPIREAT,
PTTL, RANDOMKEY, RENAME, RENAMENX, RESTORE, SORT, TOUCH, TTL, UNLINK, WAIT

Won't implement:
# KEYS not implemented, from docs Warning: consider KEYS as a command that should only be used in production environments with extreme care
# SCAN not implemented, will be hard to maintain the cursor and sequence of existing and newly added keys
'''


# TODO: must add constraints on inputs, annotations + typeguard @typechecked should be sufficient
###################
# String Commands #
###################
@run_methods_return_type(bool)
@run_method_is_safe
class AssertType(TypeCheck):
    """
    This is not part of RESP, it's a RediSnap add-on, it does deep type
    inspection.

    >>> ex.purge()
    >>> ex(Set('foo', 'bar'))
    >>> ex(AssertType('foo', RScalar))
    True
    >>> ex(AssertType('foo', RHash))
    False

    NOTE: This is the exact same implementation in local and redis backends
    """
    @auto_set_fields
    def __init__(self, key: str, r_type: RESPType):
        pass

    # to_data_dependency(self):
    #     return ExactTypeDependancy(self.key)


@run_methods_return_type(type(None))
class AppendWO(Mutate):
    """
    >>> ex.purge()
    >>> ex(AppendWO('foo', 'abc')); ex(Get('foo'))
    RScalar('abc')
    >>> ex(AppendWO('foo', 'abc')); ex(Get('foo'))
    RScalar('abcabc')

    >>> ex(AppendWO('fooint', '1')); ex(Get('fooint'))
    RScalarInt(1)
    >>> ex(AppendWO('fooint', '1')); ex(Get('fooint'))
    RScalarInt(11)
    """
    @auto_set_fields
    def __init__(self, key: str, value: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RScalar))
        return ex(self)


@run_methods_return_type(bytes)
class Get(Read):
    """
    >>> _ = ex.purge()
    >>> ex(Get('foo'))
    RDoesNotExist()
    """
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RScalar))
        return ex(self)


@run_methods_return_type(type(None))
@run_method_is_safe
class Set(Write):
    """
    TODO: Rename Set_
    >>> _ = ex.purge()
    >>> ex(Set('foo', 'bar'))

    >>> ex(Exists('foo'))
    True

    >>> ex(Type('foo')).__name__; ex(Get('foo'))
    'RScalar'
    RScalar('bar')

    >>> _ = ex(Set('foo', 1)); ex(Type('foo')).__name__; ex(Get('foo'))
    'RScalar'
    RScalarInt(1)
    """
    @auto_set_fields
    def __init__(self, key: str, value: Union[str, float, int]):
        pass

# Note: Front end must convert Incr, Decr, and DecrBy to IncrBy
@run_methods_return_type(int)
class IncrByWO(Mutate):
    """
    >>> ex.purge()

    Increment an empty key
    >>> ex(IncrByWO('foo', 1));

    >>> ex(Get('foo'))
    RScalarInt(1)

    Increment an existing key
    >>> ex(IncrByWO('foo', 1));

    >>> ex(Get('foo'))
    RScalarInt(2)

    Incremenent non-int scalars
    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, IncrByWO('foo', 1))
    ('RedisVauleTypeError', 'Existing value has wrong type.')

    >>> ex(Set('foo', 1.0))
    >>> return_exception_tuple(ex, IncrByWO('foo', 1))
    ('RedisVauleTypeError', 'Existing value has wrong type.')
    """

    @auto_set_fields
    def __init__(self, key, amount: int):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RScalarInt))
        return ex(self)


#################
# Hash Commands #
#################
@run_methods_return_type(bool)
@run_method_is_safe
class AssertFieldType(TypeCheck):
    '''
    This is not part of RESP, it's a RediSnap add-on, it does deep type
    inspection.

    NOTE: Very important, In Redis empty fields are fully polymorphic, so
    asserting any type on non-existent key will always succeed. This is how
    Redis behaves:
    > get some_non_existent_key
    (nil)

    Only if an existing value exists of the wrong type is there a problem:
    > set some_string abc
    OK
    > hget some_string field_name
    (error) WRONGTYPE Operation against a key holding the wrong kind of value

    TODO: Add a test for this command
    >> ex(AssertFieldType('foo', 'bar', RScalar))
    '''
    @auto_set_fields
    def __init__(self, key: str, field: str, r_type: RESPType):
        self.safe_run = self.run


@run_methods_return_type(bytes)
class HGet(Read):
    """
    >>> ex.purge()
    >>> ex(HGet('foo', 'bar'))
    RDoesNotExist()
    """
    @auto_set_fields
    def __init__(self, key: str, field: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RHash))
        return ex(self)

#@run_methods_return_type(type(None))
class HSet(Write):
    """
    >>> ex.purge()
    >>> ex(HSet('foo', 'bar', 'baz'))
    >>> ex(HGet('foo', 'bar'))
    RScalar('baz')

    >>> ex(HSet('foo', 'bar', 1))
    >>> ex(HGet('foo', 'bar'))
    RScalarInt(1)
    """
    @auto_set_fields
    def __init__(self, key: str, field: str, value: Union[str, float, int]):
        pass

    def safe_run(self, ex):
        # Just assert that the key has
        assert ex(AssertType(self.key, RHash))
        return ex(self)

class HExists(Read):
    """
    >>> ex.purge()
    >>> ex(HExists('foo', 'bar'))
    False

    >>> ex(HSet('foo', 'bar', 'baz'))
    >>> ex(HExists('foo', 'bar'))
    True

    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, HExists('foo', 'bar'))
    ('RedisKeyTypeError', 'Existing value has wrong type.')
    """
    @auto_set_fields
    def __init__(self, key: str, field: str):
        pass

    def safe_run(self, ex):
        # Just assert that the key has
        assert ex(AssertType(self.key, RHash))
        return ex(self)

#################
# List Commands #
#################
class LLen(Read):
    """
    TODO: add test for llen
    >> ex(LLen('foo'))
    """
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LIndex(Read):
    """
    >>> ex.purge()

    >>> ex(RPushNR('foo', ['bar']))
    >>> ex(LIndex('foo', 0))
    RScalar('bar')

    >>> ex(LIndex('foo', 20))
    RDoesNotExist()

    >>> ex.purge()

    >>> ex(LIndex('foo', 0))
    RDoesNotExist()

    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, LIndex('foo', 0))
    ('RedisKeyTypeError', 'Existing value has wrong type.')
    """
    @auto_set_fields
    def __init__(self, key: str, index: int):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LSet(Write):
    """
    >>> ex.purge()
    >>> return_exception_tuple(ex, LSet('foo', 0, 'bar'))
    ('RedisKeyTypeError', 'Cannot LSet an nonexistent key.')

    >>> ex(RPushNR('foo', ['bar']))
    >>> ex(LSet('foo', 0, 'baz'))

    >>> return_exception_tuple(ex, LSet('foo', 1, 'bar'))
    ('RedisListOutOfRange', 'Index out of range.')
    """
    @auto_set_fields
    def __init__(self, key: str, index: int, value: Union[str, float, int]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        list_len = ex(LLen(self.key))
        assert list_len > self.index
        return ex(self)


class LPushNR(Mutate):
    """
    >>> ex.purge()
    >>> ex(LPushNR('foo', ['bar']))
    >>> ex(LIndex('foo', 0))
    RScalar('bar')

    >>> ex(LPushNR('foo', ['baz']))
    >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
    RScalar('baz')
    RScalar('bar')

    >>> ex.purge()
    >>> ex(LPushNR('foo', ['bar', 'baz']))
    >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
    RScalar('baz')
    RScalar('bar')
    """
    @auto_set_fields
    def __init__(self, key: str, value: List[Union[str, float, int]]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class RPushNR(Mutate):
    """
    >>> ex.purge()
    >>> ex(RPushNR('foo', ['bar']))
    >>> ex(LIndex('foo', 0))
    RScalar('bar')

    >>> ex(RPushNR('foo', ['baz']))
    >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
    RScalar('bar')
    RScalar('baz')


    >>> ex.purge()
    >>> ex(RPushNR('foo', ['bar', 'baz']))
    >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
    RScalar('bar')
    RScalar('baz')
    """
    @auto_set_fields
    def __init__(self, key: str, value: List[Union[str, float, int]]):
        pass

    def safe_run(self, ex):
        raise NotImplementedError()
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LPop(Mutate, Read):
    """
    >>> ex.purge()
    >>> ex(LPop('foo'))
    RDoesNotExist()

    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, LPop('foo'))
    ('RedisKeyTypeError', 'Existing value has wrong type.')

    >>> ex.purge()
    >>> ex(LPushNR('foo', ['bar', 'baz']))
    >>> ex(LPop('foo')); ex(LPop('foo'))
    RScalar('baz')
    RScalar('bar')
    """
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class RPop(Mutate, Read):
    """
    >>> ex.purge()
    >>> ex(RPushNR('foo', ['bar', 'baz']))
    >>> ex(RPop('foo')); ex(RPop('foo'))
    RScalar('baz')
    RScalar('bar')
    """
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)

class ZAddNR(Mutate):
    """
    >>> ex.purge()

    # Testing auto creation
    >>> ex(ZAddNR('foo', 1, 'bar'))
    >>> ex(ZScore('foo', 'bar'))
    1

    # Testing modification of an existing value
    >>> ex(ZAddNR('foo', 2, 'baz'))
    >>> ex(ZScore('foo', 'bar'));  ex(ZScore('foo', 'baz'))
    1
    2

    # Testing update of an existing member
    >>> ex(ZAddNR('foo', 50, 'baz'))
    >>> ex(ZScore('foo', 'bar')); ex(ZScore('foo', 'baz'))
    1
    50

    # Testing exception on type mismatch
    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, ZAddNR('foo', 2, 'baz'))
    ('RedisKeyTypeError', 'Existing value has wrong type.')
    """
    @auto_set_fields
    def __init__(self, key: str, score: str, member: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZRemNR(Mutate):
    """
    >>> ex.purge()

    Testing zrem on non existing key
    >>> ex(ZRemNR('foo', 'bar'))
    >>> ex(Exists('foo'))
    False

    Test modification of existing
    >>> ex(ZAddNR('foo', 1, 'bar'))
    >>> ex(ZAddNR('foo', 2, 'baz'))
    >>> ex(ZRemNR('foo', 'baz'))
    >>> ex(ZScore('foo', 'bar')); ex(ZScore('foo', 'baz'))
    1

    Test zrem of non-existent member
    >>> ex(ZRemNR('foo', 'qux'))

    Test deletion of sset after last member is removed
    >>> ex(ZRemNR('foo', 'bar'))
    >>> ex(Exists('foo'))
    False

    # Testing exception on type mismatch
    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, ZRemNR('foo', 'qux'))
    ('RedisKeyTypeError', 'Existing value has wrong type.')
    """
    @auto_set_fields
    def __init__(self, key: str, member: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZRevRangeByScore(Read):
    """
    Removes the specified members from the sorted set stored at key. Non existing members are ignored.
    >>> ex.purge()
    >>> ex(ZAddNR('foo', 1, 'one')); ex(ZAddNR('foo', 2, 'two')); ex(ZAddNR('foo', 3, 'three'))
    >>> list(ex(ZRevRangeByScore('foo',None,None)))
    ['three', 'two', 'one']

    >>> list(ex(ZRevRangeByScore('foo', 2, 1)))
    ['two', 'one']

    >>> list(ex(ZRevRangeByScore('foo', 2, 1, (False, True))))
    ['two']

    >>> list(ex(ZRevRangeByScore('foo', 2, 1, (False, False))))
    []

    # Testing exception on type mismatch
    >>> ex(Set('foo', 'bar'))
    >>> return_exception_tuple(ex, ZRevRangeByScore('foo',10,30))
    ('RedisKeyTypeError', 'Existing value has wrong type.')
    """
    @auto_set_fields
    def __init__(self, key: str, min: int, max: int, inclusive=(True, True), with_scores=False):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZScore(Read):
    @auto_set_fields
    def __init__(self, key: str, member: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZIncrByNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, member: str, amount:int):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


# TODO: refactor this and the function below
def merge_write_commands(to_merge, merged_on):
    """
    TODO: Important: as commands are added, this function must be updated.
    """
    supported_commands = [Set]
    assert type(to_merge) in supported_commands, "Unsupported command"
    assert type(merged_on) in supported_commands, "Unsupported command"
    assert to_merge.key == merged_on.key, "Cannot merge, keys don't match"

    if type(to_merge) == Set:
        return to_merge

    raise Exception('Unsupport combination of commands.')


def merge_read_commands(to_merge, merged_on):
    """
    TODO: Important: as commands are added, this function must be updated.
    """
    supported_commands = [Get]
    assert type(to_merge) in supported_commands, "Unsupported command"
    assert type(merged_on) in supported_commands, "Unsupported command"
    assert to_merge.key == merged_on.key, "Cannot merge, keys don't match"

    if type(to_merge) == Get:
        return to_merge

    raise Exception('Unsupport combination of commands.')



'''
TODO:
* Bitmaps Commands
* hyperloglogs Commands
'''

"""
Note: This module currently holds shared tests for RediSnap
"""

def run_tests(deps_provider):
    import seneca.engine.storage.redisnap.local_backend as l_back
    import seneca.engine.storage.redisnap.redis_backend as r_back

    from seneca.engine.util import return_exception_tuple

    import doctest, sys

    # Setup up three executers
    executers = [l_back.Executer()] #, r_back.Executer(host='127.0.0.1', port=32768)]

    ret = lambda: None
    ret.attempted = 0
    ret.failed = 0

    for ex in executers:
        mod_name = ex.__module__
        print("-- Testing executer %s --\n" % type(ex))
        res = doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
        ret.failed += res.failed
        ret.attempted += res.attempted
        print("-- Done with %s --\n" % type(ex))

    return ret
