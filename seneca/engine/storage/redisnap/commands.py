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
from typing import Union

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
class Write(Command): pass
class Mutate(Command): pass


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
    """
    @auto_set_fields
    def __init__(self, key):
        pass

@run_methods_return_type(bool)
@run_method_is_safe
class Exists(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

@run_methods_return_type(type(None))
@run_method_is_safe
class Del(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

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
    '''
    This is not part of RESP, it's a RediSnap add-on, it does deep type
    inspection.
    '''
    @auto_set_fields
    def __init__(self, key: str, r_type: RESPType):
        pass
        #self.safe_run = self.run




@run_methods_return_type(type(None))
class AppendWO(Mutate):
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
class Set(Write):
    @auto_set_fields
    def __init__(self, key: str, value: Union[str, float, int]):
        pass

# Note: Front end must convert Incr, Decr, and DecrBy to IncrBy
@run_methods_return_type(int)
class IncrByWO(Mutate):
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
    '''
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
class HSet(Write):
    @auto_set_fields
    def __init__(self, key: str, field: str, value: Union[str, float, int]):
        pass

    def safe_run(self, ex):
        # Just assert that the key has
        assert ex(AssertType(self.key, RHash))
        return ex(self)


# class BitCount(Reads, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, start=None, end=None):
#         pass

# BITFIELD, not implemented
#
# class BitOp(Reads, Writes, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, operation, dest, *keys):
#         pass
#
# class BitPos(Reads, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, bit, start=None, end=None):
#         pass
#
# class GetBit(Reads, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, offset):
#         pass
#
# class GetRange(Reads, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, start, end):
#         pass
#
# class GetSet(Reads, Writes, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, start, end):
#         pass


# TODO: decide if we actually want floats in Redis, could be a source of non-determinism
# class IncrByFloat(Reads, Writes, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, amount):
#         pass
#
# class MGet(Reads, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, keys):
#         pass
#
# class MSet(Writes, RESPString):
#     @auto_set_fields
#     def __init__(self, kv_dict):
#         pass
#
# class MSetNX(Reads, Writes, RESPString):
#     @auto_set_fields
#     def __init__(self, kv_dict):
#         pass

# PSETEX not implementing


# class SetBit(Writes, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, offset, value):
#         pass

# SETEX not implemented
#
# class SetNX(Reads, Writes, RESPString):
#     @auto_set_fields
#     def __init__(self, key, value):
#         pass
#
# class SetRange(Writes, is_dependant_on(RESPString)):
#     @auto_set_fields
#     def __init__(self, key, offset, value):
#         pass

# class StrLen(Reads):
#     @auto_set_fields
#     def __init__(self, key, offset, value):
#         pass
#
#     def verify_runnable(self, executer):
#         return issubclass(ex(Type(self.key)), rtypes.RScalar)


"""
# Hash Commands #
class HDel(TypeDependantWrites, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, fields):
        pass

class HExists(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HGet(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HGetAll(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key):
        pass

class HIncrBy(TypeDependantWrites, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field, amount):
        pass

class HIncrByFloat(TypeDependantWrites, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class HKeys(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key):
        pass

class HLen(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key):
        pass

class HMGet(Reads, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, fields):
        pass

class HMSet(TypeDependantWrites, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, kv_dict):
        pass

# HScan - not implemented

class HSet(TypeDependantWrites, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field, value):
        pass

class HSetNX(Writes, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field, value):
        pass

class HStrLen(Command, RESPHashMap):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HVals(Command, RESPHashMap):
    @auto_set_fields
    def __init__(self, key):
        pass
"""
'''
TODO:
* List Commands
* Sets Commands
* OrderedSets Commands
* Bitmaps Commands
* hyperloglogs Commands
'''


def run_tests(deps_provider):
    '''
    Test basics of Set
    >> s = Set('a', 'b')
    >> s.__dict__
    {'key': 'a', 'value': 'b'}
    >> s.run.__annotations__
    {'return': <class 'NoneType'>}

    Test polymorphic scalars

    >> _ = Get('a')

    Test basics of Incr
    >> i = IncrBy('a', 1)
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
