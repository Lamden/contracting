from seneca.engine.util import auto_set_fields
from abc import ABCMeta, abstractmethod
import inspect
from collections import deque


class RedisKeyTypeError(Exception):
    pass

class ReprIsConstructor(metaclass=ABCMeta):
    def __repr__(self):
        #return '<RESP ADDRESS (%s) %s>' % (self.__class__.__name__, str(self.__dict__))
        args = list(inspect.signature(self.__class__.__init__).parameters.keys())[1:]
        auto_constructor_args = ', '.join(map(repr, [getattr(self, a) for a in args]))
        return '%s(%s)' % (self.__class__.__name__, auto_constructor_args)


## Data types ##
class RESPType(ReprIsConstructor):
    @auto_set_fields
    def __init__(self):
        pass

# Scalar Types
# TODO: to_bytes() methods for RScalar data types.
class RScalar(RESPType):
    @auto_set_fields
    def __init__(self, value):
        pass

    def to_bytes(self):
        return str.encode(self.value)

class RScalarInt(RScalar):
    def to_bytes(self):
        return str.encode(str(self.value))

class RScalarFloat(RScalar):
    def to_bytes(self):
        return str.encode(str(self.value))

class RList(RESPType):
    def __init__(self, data_list):
        self.data = deque(data_list)

    def __repr__(self):
        return 'RList(%s)' % self.data

class RSet(RESPType): pass
class RSortedSet(RESPType): pass

# Collections
class RHash(RESPType):
    @auto_set_fields
    def __init__(self, data):
        pass

class RDoesNotExist(RScalarInt, RScalarFloat, RHash, RList, RSet, RSortedSet):
    """
    In Redis nonexistent keys are fully polymorphic.
    These must be stored in addresses after we do a del, so reads don't fall through and create a spurious dependency.

    >>> RDoesNotExist()
    RDoesNotExist()

    >>> RScalar('a')
    RScalar('a')

    >>> RScalarInt(7)
    RScalarInt(7)

    """
    @auto_set_fields
    def __init__(self):
        pass

    def __repr__(_):
        return 'RDoesNotExist()'

class DataDependancy(ReprIsConstructor):
    @auto_set_fields
    def __init__(self, key):
        pass

class ExistentialDependancy(ReprIsConstructor):
    pass

class GeneralTypeDependancy(DataDependancy):
    pass

class ExactTypeDependancy(DataDependancy):
    pass

class KeyReadDependancy(DataDependancy):
    pass

class HashFieldReadDependancy(DataDependancy):
    @auto_set_fields
    def __init__(self, key, field):
        pass

def make_rscalar(val):
    if val is None:
        return RDoesNotExist()
    if isinstance(val, int):
        return RScalarInt(val)
    elif isinstance(val, float):
        return RScalarFloat(val)
    else:
        try:
            i = int(val)
            return RScalarInt(i)
        except ValueError:
            pass

        try:
            f = float(val)
            return RScalarFloat(f)
        except ValueError:
            pass

        assert isinstance(val, str)
        return RScalar(val)

def from_resp_str(type_byte_str):
    d = { 'string': RScalar,
          'hash': RHash,
          'none': RDoesNotExist
          # TODO: Finish this.
        }
    assert type_byte_str in d
    return d[type_byte_str]

def run_tests(deps_provider):
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
