from seneca.engine.util import auto_set_fields, fst, snd, swap
from abc import ABCMeta, abstractmethod
import inspect
from collections import deque
from sortedcontainers import SortedSet


class RedisKeyTypeError(Exception):
    pass

class RedisVauleTypeError(Exception):
    pass

class RedisListOutOfRange(Exception):
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


class RSortedSet(RESPType):
    def __init__(self, score_element_pair_list):
        self._sorted_set = SortedSet(score_element_pair_list, key=fst)
        self._dict = dict(map(swap, score_element_pair_list))

    def __repr__(self):
        """
        >>> RSortedSet([(1, 'foo'), (2, 'bar')])
        RSortedSet([(1, 'foo'), (2, 'bar')])
        """
        return 'RSortedSet(%s)'  % str(list(sorted(map(swap, self._dict.items()), key=fst)))

    def add(self, score, elememnt):
        """
        >>> s = RSortedSet([])
        >>> s.add(1,'foo'); s
        RSortedSet([(1, 'foo')])

        >>> s.add(2,'bar'); s
        RSortedSet([(1, 'foo'), (2, 'bar')])
        """
        self._sorted_set.add((score, elememnt))
        self._dict[elememnt] = score

    def rem(self, element):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.rem('foo'); s
        RSortedSet([(2, 'bar')])
        >>> s.rem('bar'); s
        RSortedSet([])

        >>> return_exception_tuple(s.rem, ('bar'))
        ('KeyError', "'bar'")
        """
        score = self._dict.pop(element)
        self._sorted_set.discard((score, element))

    def rev_range_by_score(self, min_:int, max_:int, inclusive=(True,True)):
        """
        ZRANGEBYSCORE zset (1 5
        Will return all elements with 1 < score <= 5 while:

        >>> list(RSortedSet([(1, 'foo'), (2, 'bar')]).rev_range_by_score(1,1))
        ['foo']

        >>> list(RSortedSet([(1, 'foo'), (2, 'bar')]).rev_range_by_score(3,5))
        []

        >>> list(RSortedSet([(1, 'foo'), (2, 'bar')]).rev_range_by_score(2,1))
        []

        >>> list(RSortedSet([(1, 'foo'), (2, 'bar')]).rev_range_by_score(1,2, (True,False)))
        ['foo']

        >>> list(RSortedSet([(1, 'foo'), (2, 'bar')]).rev_range_by_score(1,2, (False,False)))
        []
        """
        return map(snd, self._sorted_set.irange((min_, None), (max_, None), inclusive=inclusive))

    def score(self, element):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.score('foo')
        1
        >>> s.score('bar')
        2

        >>> s.score('baz')
        """
        try:
            return self._dict[element]
        except KeyError:
            return None

    def incr_by(self, element, amount):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.incr_by('foo', 1); s.score('foo')
        2
        >>> s.incr_by('foo', 2); s.score('foo')
        4
        >>> s
        RSortedSet([(2, 'bar'), (4, 'foo')])

        >>> s.incr_by('new_element', 2); s.score('new_element')
        2
        """
        score = self._dict.pop(element, 0)
        self._sorted_set.discard((score, element))

        new_score = score + amount
        self._dict[element] = new_score
        self._sorted_set.add((new_score, element))


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
    def return_exception(*args):
        try:
            return args[0](*args[1:])
            raise Exception("This test expected an exception but no exception was thrown!")
        except Exception as e:
            return e

    def return_exception_tuple(*args):
        e = return_exception(*args)
        return (type(e).__name__, str(e))

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
