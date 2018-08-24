from abc import ABCMeta, abstractmethod
from typing import Union

from seneca.engine.util import auto_set_fields
from seneca.engine.storage.redisnap.resp_types import *
from seneca.engine.storage.redisnap.addresses import *

# TODO: Enforce run return types for run method in executer libs.

class Command(metaclass=ABCMeta):
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

    def __repr__(self):
        return '<RESP (%s) %s>' % (self.__class__.__name__, str(self.__dict__))

    @abstractmethod
    def safe_run(self, local_ex):
        pass

class TypeCheck(Command): pass
class Read(Command): pass
class Write(Command): pass


#NOTE: This is a decorator function, not a class!
class run_methods_return_type:
    '''
    '''
    @auto_set_fields
    def __init__(self, t):
        pass

    def __call__(self, cls):
        cls.run.__annotations__['return'] = self.t
        return cls


#NOTE: This is a decorator function, not a class!
def run_method_is_safe(cls):
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
    def __init__(self, addr):
        pass

@run_methods_return_type(bool)
@run_method_is_safe
class Exists(Command):
    @auto_set_fields
    def __init__(self, addr):
        pass

@run_methods_return_type(type(None))
@run_method_is_safe
class Del(Command):
    @auto_set_fields
    def __init__(self, addr):
        pass


# DUMP not implemented
# EXPIRE not implemented
# EXPIREAT not implemented
# KEYS not implemented, from docs Warning: consider KEYS as a command that should only be used in production environments with extreme care
# MIGRATE not implemented
# MOVE not implemented
# OBJECT not implemented
# PERSIST not implemented
# PEXPIRE not implemented
# PEXPIREAT not implemented
# PTTL not implemented
# RANDOMKEY not implemented
# RENAME
# RENAMENX
# RESTORE not implemented
# SCAN not implemented, will be hard to maintain the cursor and sequence of existing and newly added keys
# SORT not implemented
# TOUCH not implemented
# TTL not implemented
# UNLINK
# WAIT not implemented


# TODO: must add constraints on inputs, annotations + typeguard @typechecked should be sufficient
###################
# String Commands #
###################
@run_methods_return_type(bool)
@run_method_is_safe
class AssertType(TypeCheck):
    '''
    This is not part of RESP, it's a RediSnap add-on, it does deep type inspection
    '''
    @auto_set_fields
    def __init__(self, addr: Address, r_type: RESPType):
        self.safe_run = self.run

@run_methods_return_type(int)
class Append(Write):
    @auto_set_fields
    def __init__(self, addr: ScalarAddress, value: str):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.addr, RScalar))
        ex(self)

@run_methods_return_type(bytes)
class Get(Read):
    @auto_set_fields
    def __init__(self, addr: ScalarAddress):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.addr, RScalar))
        ex(self)

@run_methods_return_type(type(None))
@run_method_is_safe
class Set(Write):
    @auto_set_fields
    def __init__(self, addr: ScalarAddress, value: Union[str, float, int]):
        pass


# Note: Front end must convert Incr, Decr, and DecrBy to IncrBy
@run_methods_return_type(int)
class IncrBy(Write):
    @auto_set_fields
    def __init__(self, addr, amount: int):
        pass

    def safe_run(self, ex):
        assert ex(AssertType(self.addr, RScalarInt))
        ex(self)


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

# TODO: List Commands #
# TODO: Sets Commands #
# TODO: OrderedSets Commands #
# TODO: Bitmaps Commands #
# TODO: hyperloglogs Commands #
"""



def run_tests(deps_provider):
    '''
    Test basics of Set
    >>> s = Set('a', 'b')
    >>> s.__dict__
    {'addr': 'a', 'value': 'b'}
    >>> s.run.__annotations__
    {'return': <class 'int'>}

    Test polymorphic scalars

    >>> _ = Get('a')

    Test basics of Incr
    >>> i = IncrBy('a', 1)
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
