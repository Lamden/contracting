from seneca.engine.util import auto_set_fields


class Command:
    # Todo: methods that serialize
    pass

class WriteCommand(RedisCommand):
    pass

# May not be needed
# class MultiWrite(RedisCommand):
#     # list of writes
#     pass


# String Commands #
class Append(WriteCommand):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class BitCount(WriteCommand):
    @auto_set_fields
    def __init__(self, key, start=None, end=None):
        pass

# BITFIELD, not implemented

class BitOp(WriteCommand):
    @auto_set_fields
    def __init__(self, operation, dest, *keys):
        pass

class BitPos(Command):
    @auto_set_fields
    def __init__(self, key, bit, start=None, end=None):
        pass

class Decr(WriteCommand):
    @auto_set_fields
    def __init__(self, key):
        pass

class DecrBy(WriteCommand):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class Get(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

class GetBit(Command):
    @auto_set_fields
    def __init__(self, key, offset):
        pass

class GetRange(Command):
    @auto_set_fields
    def __init__(self, key, start, end):
        pass

class GetSet(WriteCommand):
    @auto_set_fields
    def __init__(self, key, start, end):
        pass

class Incr(WriteCommand):
    @auto_set_fields
    def __init__(self, key):
        pass

class IncrBy(WriteCommand):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class IncrByFloat(WriteCommand):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class MGet(Command):
    @auto_set_fields
    def __init__(self, keys):
        pass

class MSet(WriteCommand):
    @auto_set_fields
    def __init__(self, kv_dict):
        pass

class MSetNX(WriteCommand):
    @auto_set_fields
    def __init__(self, kv_dict):
        pass

# PSETEX not implementing

class Set(WriteCommand):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class SetBit(WriteCommand):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

# SETEX not implemented

class SetNX(WriteCommand):
    @auto_set_fields
    def __init__(self, key, value):
        pass

class SetRange(WriteCommand):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

class StrLen(Command):
    @auto_set_fields
    def __init__(self, key, offset, value):
        pass

# Hash Commands #
class HDel(WriteCommand):
    @auto_set_fields
    def __init__(self, key, fields):
        pass

class HExists(Command):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HGet(Command):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HGetAll(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

class HIncrBy(WriteCommand):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class HIncrByFloat(WriteCommand):
    @auto_set_fields
    def __init__(self, key, amount):
        pass

class HKeys(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

class HLen(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

class HMGet(Command):
    @auto_set_fields
    def __init__(self, key, fields):
        pass

class HMSet(WriteCommand):
    @auto_set_fields
    def __init__(self, key, kv_dict):
        pass

class HScan(Command):
    @auto_set_fields
    def __init__(self, key, iterator):
        pass

class HSet(WriteCommand):
    @auto_set_fields
    def __init__(self, key, field, value):
        pass

class HSetNX(WriteCommand):
    @auto_set_fields
    def __init__(self, key, field, value):
        pass

class HStrLen(Command):
    @auto_set_fields
    def __init__(self, key, field):
        pass

class HVals(Command):
    @auto_set_fields
    def __init__(self, key):
        pass

# TODO: List Commands #
# TODO: Sets Commands #
# TODO: OrderedSets Commands #
