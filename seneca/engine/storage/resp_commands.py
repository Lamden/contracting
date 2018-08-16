from abc import ABCMeta, abstractmethod

from seneca.engine.util import auto_set_fields

class RESPType(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def resp_type():
        raise NotImplementedError

class RESPKey(RESPType): pass
class RESPString(RESPType): pass
class RESPList(RESPType): pass
class RESPHashMap(RESPType): pass
class RESPSet(RESPType): pass
class RESPSortedSet(RESPType): pass
class RESPBitmap(RESPType): pass
class RESPHyperLogLog(RESPType): pass


class Command(metaclass=ABCMeta):
    pass

class Reads(Command):
    pass

class Writes(Command):
    pass

class TypeDependant():
    '''
    Depends on type of previously written value
    '''
    pass


# Memoize this
def is_dependant_on(resp_type):
    return type(
    'Foo', # Fix this
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

# EXISTS

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

# TYPE

# UNLINK not implemented, asynchronous
# WAIT not implemented

# String Commands #
class Append(Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class BitCount(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, start=None, end=None):
        pass

# BITFIELD, not implemented

class BitOp(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, operation, dest, *keys):
        pass

class BitPos(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, bit, start=None, end=None):
        pass

class Decr(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key):
        pass

class DecrBy(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class Get(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key):
        pass

class GetBit(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, offset):
        pass

class GetRange(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, start, end):
        pass

class GetSet(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, start, end):
        pass

class Incr(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key):
        pass

class IncrBy(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class IncrByFloat(Reads, Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class MGet(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, keys):
        pass

class MSet(Writes, RESPString):
    @auto_set_fields
    def __init__(self, kv_dict):
        pass

class MSetNX(Reads, Writes, RESPString):
    @auto_set_fields
    def __init__(self, kv_dict):
        pass

# PSETEX not implementing

class Set(Writes, RESPString):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class SetBit(Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

# SETEX not implemented

class SetNX(Reads, Writes, RESPString):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class SetRange(Writes, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

class StrLen(Reads, is_dependant_on(RESPString)):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

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
