from seneca.engine.util import auto_set_fields
from abc import ABCMeta, abstractmethod
import inspect

class ReprIsConstructor(metaclass=ABCMeta):
    def __repr__(self):
        #return '<RESP ADDRESS (%s) %s>' % (self.__class__.__name__, str(self.__dict__))
        args = list(inspect.signature(self.__class__.__init__).parameters.keys())[1:]
        auto_constructor_args = ', '.join(map(repr, [getattr(self, a) for a in args]))
        return '%s(%s)' % (self.__class__.__name__, auto_constructor_args)


# ## Addres types##
# class Address(ReprIsConstructor):
#     '''
#     >>> ScalarAddress('key_is_something')
#     ScalarAddress('key_is_something')
#
#     >>> RHashFieldAddress('key_str', 'field_str')
#     RHashFieldAddress('key_str', 'field_str')
#
#     '''
#     @auto_set_fields
#     def __init__(self, key):
#         pass
#
#     def base_address(self):
#         """
#         Address can reference sub-items in containers e.g. fields in hashmaps.
#         This method returns the container's address. For simple typles it just
#         returns self.
#         """
#         raise Exception('Address is lowest level, already base.')
#
#
#
# class ScalarAddress(Address): pass
# class RHashAddress(Address): pass
#
# class RHashFieldAddress(Address):
#     @auto_set_fields
#     def __init__(self, key, field):
#         pass
#
#     def base_address(self):
#         return self.key

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
class RScalarInt(RScalar): pass
class RScalarFloat(RScalar): pass

class RList(RESPType): pass
class RSet(RESPType): pass
class RSortedSet(RESPType): pass

# Collections
class RHash(RESPType):
    @auto_set_fields
    def __init__(self, value):
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


def make_rscalar(val):
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



def run_tests(deps_provider):
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
