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
"""
from abc import ABCMeta, abstractmethod
from typing import Union, List, Dict

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
    @auto_set_fields
    def __init__(self, key):
        pass


@run_methods_return_type(bool)
@run_method_is_safe
class Exists(Command):
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
    @auto_set_fields
    def __init__(self, key: str, r_type: RESPType):
        pass


@run_methods_return_type(type(None))
class AppendNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, value: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RScalar))
        return ex(self)


@run_methods_return_type(bytes)
class Get(Read):
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RScalar))
        return ex(self)


@run_methods_return_type(type(None))
@run_method_is_safe
class SetNR(Write):
    @auto_set_fields
    def __init__(self, key: str, value: Union[str, float, int]):
        pass

# Note: Front end must convert Incr, Decr, and DecrBy to IncrBy
@run_methods_return_type(int)
class IncrByNR(Mutate):
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
    @auto_set_fields
    def __init__(self, key: str, field: str, r_type: RESPType):
        self.safe_run = self.run


@run_methods_return_type(bytes)
class HGet(Read):
    @auto_set_fields
    def __init__(self, key: str, field: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RHash))
        return ex(self)

#@run_methods_return_type(type(None))
class HSetNR(Write):
    @auto_set_fields
    def __init__(self, key: str, field: str, value: Union[str, float, int]):
        pass

    def safe_run(self, ex):
        # Just assert that the key has
        assert ex(AssertType(self.key, RHash))
        return ex(self)

class HExists(Read):
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

    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LIndex(Read):
    @auto_set_fields
    def __init__(self, key: str, index: int):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LSet(Write):
    @auto_set_fields
    def __init__(self, key: str, index: int, value: Union[str, float, int]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        list_len = ex(LLen(self.key))
        assert list_len > self.index
        return ex(self)


class LPushNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, value: List[Union[str, float, int]]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class RPushNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, value: List[Union[str, float, int]]):
        pass

    def safe_run(self, ex):
        raise NotImplementedError()
        assert ex(AssertType(self.key, RList))
        return ex(self)


class LPop(Mutate, Read):
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)


class RPop(Mutate, Read):
    @auto_set_fields
    def __init__(self, key: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RList))
        return ex(self)

class ZAddNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, members_and_scores: Dict[str, int]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZRemNR(Mutate):
    @auto_set_fields
    def __init__(self, key: str, members: List[str]):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


class ZRevRangeByScore(Read):
    @auto_set_fields
    def __init__(self, key: str, max: int, min: int, inclusive=(True, True), with_scores=False):
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
    def __init__(self, key: str, amount:int, member: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.key, RSet))
        return ex(self)


# TODO: command merging
'''
TODO:
* Bitmaps Commands
* hyperloglogs Commands
'''

"""
Note: This module currently holds shared tests for RediSnap
"""

def run_tests(deps_provider):
    import doctest, sys
    from seneca.engine.util import return_exception_tuple

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
