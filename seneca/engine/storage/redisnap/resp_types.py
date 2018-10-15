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
    def __init__(self, score_member_pair_list):
        self._sorted_set = SortedSet(score_member_pair_list, key=fst)
        self._dict = dict(map(swap, score_member_pair_list))

    def __repr__(self):
        """
        >>> RSortedSet([(1, 'foo'), (2, 'bar')])
        RSortedSet([(1, 'foo'), (2, 'bar')])
        """
        return 'RSortedSet(%s)'  % str(list(sorted(map(swap, self._dict.items()), key=fst)))

    def __contains__(self, maybe_member):
        """
        >>> 'foo' in RSortedSet([(1, 'foo'), (2, 'bar')])
        True

        >>> 'baz' in RSortedSet([(1, 'foo'), (2, 'bar')])
        False
        """
        return maybe_member in self._dict

    def __len__(self):
        """
        >>> len(RSortedSet([(1, 'foo'), (2, 'bar')]))
        2

        >>> len(RSortedSet([]))
        0
        """
        return len(self._dict)

    def __bool__(self):
        """
        >>> bool(RSortedSet([(1, 'foo'), (2, 'bar')]))
        True

        >>> bool(RSortedSet([]))
        False
        """
        return bool(self._dict)

    def add(self, score, member):
        """
        >>> s = RSortedSet([])
        >>> s.add(1,'foo'); s
        RSortedSet([(1, 'foo')])

        >>> s.add(2,'bar'); s
        RSortedSet([(1, 'foo'), (2, 'bar')])
        """
        self._sorted_set.add((score, member))
        self._dict[member] = score

    def rem(self, member):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.rem('foo'); s
        RSortedSet([(2, 'bar')])
        >>> s.rem('bar'); s
        RSortedSet([])

        >>> s.rem('bar')

        """
        try:
            score = self._dict.pop(member)
            self._sorted_set.discard((score, member))
        except KeyError as e:
            pass

    def rev_range_by_score(self, max_:int, min_:int, inclusive=(True,True), with_scores=False):
        """
        TODO: add withscores
        ZRANGEBYSCORE zset (1 5
        Will return all members with 1 < score <= 5 while:

        >>> s = RSortedSet([(1, 'one'), (2, 'two'), (3, 'three')])
        >>> list(s.rev_range_by_score(None, None))
        ['three', 'two', 'one']

        >>> list(s.rev_range_by_score(2, 1))
        ['two', 'one']

        >>> list(s.rev_range_by_score(2, 1, (False, True)))
        ['one']

        >>> list(s.rev_range_by_score(2, 1, (False, False)))
        []
        """
        res = self._sorted_set.irange((min_, None), (max_, None), inclusive=swap(inclusive), reverse=True)
        if with_scores:
            return res
        else:
            return map(snd, res)

    def score(self, member):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.score('foo')
        1
        >>> s.score('bar')
        2

        >>> s.score('baz')
        """
        try:
            return self._dict[member]
        except KeyError:
            return None

    def incr_by(self, amount, member):
        """
        >>> s = RSortedSet([(1, 'foo'), (2, 'bar')])
        >>> s.incr_by(1, 'foo'); s.score('foo')
        2
        >>> s.incr_by(2, 'foo'); s.score('foo')
        4
        >>> s
        RSortedSet([(2, 'bar'), (4, 'foo')])

        >>> s.incr_by(2, 'new_member'); s.score('new_member')
        2
        """
        score = self._dict.pop(member, 0)
        self._sorted_set.discard((score, member))

        new_score = score + amount
        self._dict[member] = new_score
        self._sorted_set.add((new_score, member))


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

    def to_bytes(self):
        pass

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
    from seneca.engine.util import return_exception_tuple

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
