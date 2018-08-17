from abc import ABCMeta, abstractmethod
from seneca.engine.util import auto_set_fields
from seneca.engine.storage import resp_types as rtypes

# TODO: figure out how to enforce or at least test varying return types for run method.

class Command(metaclass=ABCMeta):
    @abstractmethod
    def run(self, ex):
        raise NotImplementedError

    # Base implementation is an empty check
    def verify_runnable(self, executer):
        return True

class Reads(Command):
    pass

class Writes(Command):
    pass


class TypeDependant():
    '''
    Depends on type of previously written value
    '''
    pass


# TODO: Memoize this
def is_dependant_on(resp_type):
    return type(
    'Foo', # TODO: Fix this
    (TypeDependant, resp_type),
    {
        'resp_type': lambda _ : resp_type # todo: try to make this a static method instead, is this needed?
    }
    )

# May not be needed
# class MultiWrite(RedisCommand):
#     # list of writes
#     pass

# Key Commands #

# DEL

# DUMP not implemented

class Exists(Reads):
    @auto_set_fields
    def __init__(self, key):
        pass
    # run returns int

class NotExists(Reads):
    @auto_set_fields
    def __init__(self, key):
        pass
    # run returns int


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

class Type(Reads):
    @auto_set_fields
    def __init__(self, key):
        pass
    # run returns rtype.Container

class ScalarType(Type):
    def verify_runnable(self, executer):
        return issubclass(ex(Type(self.key)), rtypes.RScalar)
    # run returns rtype.Container


# UNLINK
# WAIT not implemented

def must_be_scalar(self, executer):
    return issubclass(ex(Type(self.key)), rtypes.RScalar)

# String Commands #
class Append(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, value):
Append.run_requirement = must_be_scalar




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

class Incr(Reads, Writes):
    @auto_set_fields
    def __init__(self, key):
        pass

    def verify_runnable(self, executer):
        return issubclass(ex(ScalarType(self.key)), rtypes.RScalarInt)

class Decr(Incr): pass

class IncrBy(Incr):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class DecrBy(IncrBy): pass


class Get(Reads):
    @auto_set_fields
    def __init__(self, key):
        pass

    def verify_runnable(self, executer):
        return issubclass(ex(Type(self.key)), rtypes.RScalar)

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

class Set(Writes):
    @auto_set_fields
    def __init__(self, key, value):
        pass
    # No verify_runnable needed always succeeds.


#
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

class StrLen(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

    def verify_runnable(self, executer):
        return issubclass(ex(Type(self.key)), rtypes.RScalar)


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
    >>> a = Append('foo', 'bar')
    >>> isinstance(a, RESPString)
    True
    >>> isinstance(a, TypeDependant)
    True
    >>> isinstance(a, Writes)
    True
    >>> a.resp_type()
    <class 'seneca.engine.storage.resp_commands.RESPString'>
    '''
    import doctest, sys
    import seneca.smart_contract_tester as scft
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
