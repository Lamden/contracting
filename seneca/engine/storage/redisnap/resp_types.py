from seneca.engine.util import auto_set_fields
from abc import ABCMeta, abstractmethod

class RESPType():
    @auto_set_fields
    def __init__(self):
        pass
    def __repr__(self):
        return '<RESP (%s) %s>' % (self.__class__.__name__, str(self.__dict__))

# Scalar Types
class RScalar(RESPType):
    @auto_set_fields
    def __init__(self, value):
        pass
class RScalarInt(RScalar): pass
class RScalarFloat(RScalar): pass

# Collections
class RHash(RESPType):
    def __init__(self, field_value_dict):
        self.key = key
        self.fields = {k:make_rscalar(v) for k,v in field_value_dict.items()}

    def update(self, other_rhash):
        assert self.key == other_rhash.key, "The keys of the RHashes don't match, can't merge."
        self.fields.update(other_rhash.fields)
# We can have a derived type RHashField that statically has field name

class RList(RESPType):
    # Address scheme ('key', 1)
    pass

class RSet(RESPType):
    # Just key
    pass

class RSortedSet(RESPType):
    # Just key
    pass

class RDoesNotExist(RScalarInt, RScalarFloat, RHash, RList, RSet, RSortedSet):
    """
    In Redis nonexistent keys are fully polymorphic.
    These must be stored in addresses after we do a del, so reads don't fall through and create a spurious dependency.
    """
    @auto_set_fields
    def __init__(self):
        pass

    def __repr__(self):
        return '<RESP (%s) %s>' % (self.__class__.__name__, str(self.__dict__))

# TODO: Make a class for hset, may look a bit like row polymorphism

def make_rscalar(key, val):
    if isinstance(val, int):
        return RScalarInt(key, val)
    elif isinstance(val, float):
        return RScalarFloat(key, val)
    else:
        try:
            i = int(val)
            return RScalarInt(key, i)
        except ValueError:
            pass

        try:
            f = float(val)
            return RScalarFloat(key, f)
        except ValueError:
            pass

        assert isinstance(val, str)
        return RScalar(key, val)
