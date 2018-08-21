from abc import ABCMeta, abstractmethod
from typing import Union

from seneca.engine.util import auto_set_fields
from seneca.engine.storage.resp_types import *

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
    def success_requires(self, executer):
        raise NotImplementedError


class Reads(Command):
    '''
    Inheritting this class designates the command performs a read. This
    information will be used to build snapshot dependency graphs.
    '''
    pass


class Writes(Command):
    '''
    Inheritting this class designates the command performs a write. This
    information will be used to build snapshot dependency graphs.
    '''
    @abstractmethod
    def writes_type(self):
        raise NotImplementedError


# TODO: memoize this.
def writes_type(t):
    '''
    Type (i.e. class) constructor, parameterized on a type, attatches a method
    onto the created class called 'writes_type' that returns the passed type.

    Objects that inherit the outputed classes of this function have been
    designated to perform Redis writes of a specific Redis type t.
    '''
    return type(
        'WritesType_' + str(t),
        (Writes, ),
        {
            'writes_type': lambda _ : t
        }
    )


class WritesPolymorphicScalar(Writes):
    '''
    Inheritting this class designates the command performs a write to a Scalar
    (i.e. a Redis string) with the scalar's type inferred by Redis.
    '''
    def writes_type(self):
        try:
            int(str(self.value))
            return RScalarInt
        except ValueError:
            pass

        try:
            float(str(self.value))
            return RScalarFloat
        except ValueError:
            pass

        return RScalar


###############################
# Shared validation functions #
###############################
def nothing_always_succeeds(_,__):
    return True


def key_exists(self, executer):
    return Exists(self.key).run(executer)


def nx_or_existing_type_must_be(desired_type):
    '''
    Higher order function, takes a type parameter and returns a validation func.
    '''
    def f(self, executer):
        if Exists(self.key).run(executer):
            return True
        elif issubclass(GetExactType(self.key).run(executer), desired_type):
            return True
        else:
            return False

    return f


#NOTE: This is a decorator function, not a class!
class run_returns_type:
    '''
    '''
    @auto_set_fields
    def __init__(self, t):
        pass

    def __call__(self, cls):
        cls.run.__annotations__['return'] = self.t
        return cls


#NOTE: This is a decorator function, not a class!
class success_requires:
    # TODO: abstract this functionality and move to util
    '''
    '''
    @auto_set_fields
    def __init__(self, validation_function):
        pass

    def __call__(self, cls):
        if hasattr(cls, '__abstractmethods__'):
            abstr_methods = set(cls.__abstractmethods__)
            abstr_methods.remove('success_requires')
            cls.__abstractmethods__ = frozenset(abstr_methods)
        setattr(cls, 'success_requires', self.validation_function)
        return cls


################
# Key Commands #
################
@run_returns_type(RType)
@success_requires(key_exists)
class GetExactType(Reads):
    '''
    Note: Custom command for this lib, not implemented by Redis. This is here to
    Handle polymorphism in strings and hash values.
    '''
    @auto_set_fields
    def __init__(self, key: str):
        pass


@run_returns_type(RType)
@success_requires(key_exists)
class Type(Reads):
    @auto_set_fields
    def __init__(self, key: str):
        pass


@run_returns_type(bool)
@success_requires(nothing_always_succeeds)
class Exists(Reads):
    @auto_set_fields
    def __init__(self, key: str):
        pass


class NotExists(Exists): pass

# DEL
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
@run_returns_type(int) # Length of new value (I think)
@success_requires(nx_or_existing_type_must_be(RScalar))
class Append(Reads, WritesPolymorphicScalar):
    @auto_set_fields
    def __init__(self, key: str, value: str):
        pass


# Do we want to allow 'nones'?
@run_returns_type(RScalar)
@success_requires(nx_or_existing_type_must_be(RScalar))
class Get(Reads):
    @auto_set_fields
    def __init__(self, key: str):
        pass


@run_returns_type(type(None))
@success_requires(nothing_always_succeeds)
class Set(WritesPolymorphicScalar):
    @auto_set_fields
    def __init__(self, key:str , value: Union[str, float, int]):
        pass


@run_returns_type(int)
@success_requires(nx_or_existing_type_must_be(RScalarInt))
class Incr(Reads, writes_type(RScalarInt)):
    @auto_set_fields
    def __init__(self, key: str):
        pass


class Decr(Incr): pass


class IncrBy(Incr):
    @auto_set_fields
    def __init__(self, key: str, amount: int):
        pass


class DecrBy(IncrBy): pass


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
    {'key': 'a', 'value': 'b'}
    >>> s.run.__annotations__
    {'return': <class 'int'>}
    >>> s.writes_type()
    <class 'seneca.engine.storage.resp_types.RScalar'>

    Test polymorphic scalars
    >>> Set('a', 1).writes_type()
    <class 'seneca.engine.storage.resp_types.RScalarInt'>

    >>> Set('a', 1.0).writes_type()
    <class 'seneca.engine.storage.resp_types.RScalarFloat'>

    Test polymorphic scalars saved as strings
    >>> Set('a', '1').writes_type()
    <class 'seneca.engine.storage.resp_types.RScalarInt'>

    >>> Set('a', '1.0').writes_type()
    <class 'seneca.engine.storage.resp_types.RScalarFloat'>

    >>> _ = Get('a')

    Test basics of Incr
    >>> i = Incr('a')



    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
