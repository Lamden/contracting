'''
This module is a (mostly) redis-py compatible library.
* Unlike redis-py, the backend is configurable, it could write to a Redis, it
  could save the data locally.
* It generates resp command objects that are run by the backend
* It doesn't return values for incrby so incr, incrby, decr, and decrby are pure writes.
* Append doesn't return a string length; same reasoning as incrby.

Reference API: https://github.com/andymccurdy/redis-py/blob/master/redis/client.py
'''

from seneca.engine.storage.redisnap.commands import *
from seneca.engine.util import grouper

import seneca.engine.storage.redisnap.resp_types as resp_types

class Client:
    '''
    Implementation of the API provided by redis-py's StrictRedis
    '''

    def __init__(self, executer):
        self.execute_command = executer

    def _purge(self):
        return self.execute_command.purge()

    def exists(self, name):
        """
        Returns a boolean indicating whether key ``name`` exists
        >>> s._purge()
        >>> s.exists('foo')
        False
        """
        return self.execute_command(Exists(name))
    __contains__ = exists

    def type(self, name):
        """
        Returns the type of key ``name``
        >>> s._purge()
        >>> s.type('foo')
        b'none'
        """
        rtype = self.execute_command(Type(name))

        if issubclass(rtype, RDoesNotExist):
            return str.encode('none')
        elif issubclass(rtype, RScalar):
            return str.encode('string')
        elif issubclass(rtype, RHash):
            return str.encode('hash')
        else:
            raise NotImplementedError()

    def append_nr(self, key, value):
        """
        Appends the string ``value`` to the value at ``key``. If ``key``
        doesn't already exist, create it with a value of ``value``.
        Returns the new length of the value at ``key``.

        >>> s.append('foo', 'bar')
        >>> s.get('foo')
        b'bar'

        """
        return self.execute_command(Append(key, value))


    def get(self, name):
        """
        >>> s._purge()

        Return the value at key ``name``, or None if the key doesn't exist
        >>> s.get('foo') is None
        True
        """
        # TODO: Decide how we want to handle non-existing keys in the commands api
        ret = self.execute_command(Get(name))
        if isinstance(ret, RDoesNotExist):
            return None
        elif isinstance(ret, RScalar):
            return ret.to_bytes()
        else:
            raise Exception('Something went wrong.')


    def __getitem__(self, name):
        """
        Return the value at key ``name``, raises a KeyError if the key
        doesn't exist.
        """
        value = self.get(name)
        if value is not None:
            return value
        raise KeyError(name)


    def set_nr(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        >>> s._purge()

        >>> s.set_nr('foo', 'bar'); s.get('foo')
        True
        b'bar'

        >>> s.set_nr('foo', 'baz'); s.get('foo')
        True
        b'baz'

        Set the value at key ``name`` to ``value``
        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.
        ``px`` sets an expire flag on key ``name`` for ``px`` milliseconds.
        ``nx`` if set to True, set the value at key ``name`` to ``value`` only
            if it does not exist.
        ``xx`` if set to True, set the value at key ``name`` to ``value`` only
            if it already exists.
        """
        assert ex is None, 'Cache expiration not supported'
        assert px is None, 'Cache expiration not supported'
        assert nx is False # TODO: Will add this later
        assert nx is False # TODO: Will add this later

        self.execute_command(SetNR(name, value))

        return True


    def __setitem__(self, name, value):
        """
        >>> s._purge()
        >>> s['foo'] = 'bar'
        """
        self.set_nr(name, value)


    def incr_nr(self, name, amount=1):
        """
        >>> s._purge() is None
        True

        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> s.incr_nr('foo', 1) is None
        True
        """
        self.execute_command(IncrByNR(name, amount))


    def incrby_nr(self, name, amount=1):
        """
        >>> s._purge()

        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> s.incrby_nr('foo', 1) is None
        True
        """
        self.execute_command(IncrByNR(name, amount))

    def append_nr(self, name, value):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> s._purge()
        >>> s.append_nr('foo', 1) is None
        True
        """
        self.execute_command(AppendNR(name, value))


    def decr_nr(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        >>> s.decr_nr('foo', 1) is None
        True
        """
        self.execute_command(IncrByNR(name, 0 - amount))

    def hget(self, name, key):
        """
        >>> s._purge()
        >>> s.hget('foo', 'bar') is None
        True
        """
        ret = self.execute_command(HGet(name, key))
        if isinstance(ret, RDoesNotExist):
            return None
        elif isinstance(ret, RScalar):
            return ret.to_bytes()

    def hset_nr(self, name, key, value):
        """
        >>> s.hset_nr('foo', 'bar', 'baz'); s.hget('foo', 'bar')
        b'baz'
        """
        self.execute_command(HSetNR(name, key, value))


    def hexists(self, name, key):
        """
        >>> s._purge()
        >>> s.hexists('foo', 'bar')
        False

        >>> s.hset_nr('foo', 'bar', 'baz')

        >>> s.hexists('foo', 'qux')
        False

        >>> s.hexists('foo', 'bar')
        True
        """
        return self.execute_command(HExists(name, key))


    def lindex(self, name, index):
        """
        Tested in lpush_nr
        """
        return self.execute_command(LIndex(name, index)).to_bytes()



    def lpush_nr(self, name, *values):
        """
        >>> s._purge()
        >>> s.lpush_nr('foo', 'bar')

        >>> s.lindex('foo', 0)
        b'bar'

        >>> s.lindex('foo', 9)

        """
        self.execute_command(LPushNR(name, values))



    def lset(self, name, index, value):
        """
        >>> s._purge()
        >>> s.lpush_nr('foo', 'bar')
        >>> s.lset('foo', 0, 'bar')
        True

        """
        self.execute_command(LSet(name, index, value))
        return True


    def rpush_nr(self, name, *values):
        """
        >>> s._purge()
        >>> s.rpush_nr('foo', 'bar')

        >>> s.lindex('foo', 0)
        b'bar'

        """
        self.execute_command(RPushNR(name, values))


    def lpop(self, name):
        """
        >>> s._purge()
        >>> s.rpush_nr('foo', 'bar')

        >>> s.lpop('foo')
        b'bar'
        """
        return self.execute_command(LPop(name)).to_bytes()


    def rpop(self, name):
        """
        >>> s._purge()
        >>> s.rpush_nr('foo', 'bar')

        >>> s.rpop('foo')
        b'bar'
        """
        return self.execute_command(RPop(name)).to_bytes()

    def zadd_nr(self, name, *member_score_pairs, **member_score_as_kwargs):
        """
        Tested in zscore
        """
        member_scores_all = dict(grouper(member_score_pairs, 2))
        member_scores_all.update(member_score_as_kwargs)
        self.execute_command(ZAddNR(name, member_scores_all))

    def zscore(self, name, value):
        """
        >>> s._purge()
        >>> s.zadd_nr('foo', 'foo', 1, 'bar', 2, baz=3)

        >>> s.zscore('foo', 'foo')
        1
        >>> s.zscore('foo', 'bar')
        2
        >>> s.zscore('foo', 'baz')
        3
        """
        return self.execute_command(ZScore(name, value))


    def zrem_nr(self, name, *values):
        """
        >>> s._purge()
        >>> s.zadd_nr('foo', foo=1, bar=2, baz=3)
        >>> s.zrem_nr('foo', 'foo', 'bar', 'baz')
        >>> s.zscore('foo', 'foo'); s.zscore('foo', 'bar'); s.zscore('foo', 'baz');
        """
        self.execute_command(ZRemNR(name, values))


    def zrevrangebyscore(self, name, max, min, withscores=False):
        """
        >>> s._purge()
        >>> s.zadd_nr('foo', foo=1, bar=2, baz=3, qux=4, quux=5)
        >>> s.zrevrangebyscore('foo', 4, 2)
        ['qux', 'baz', 'bar']

        >>> s.zrevrangebyscore('foo', 4, 2, withscores=True)
        [(4, 'qux'), (3, 'baz'), (2, 'bar')]
        """
        # TODO: Consider not constructing list, will break API a bit, but likely more performant in some cases.
        return list(self.execute_command(ZRevRangeByScore(name, max, min, with_scores=withscores)))

    def zincrby_nr(self, name, value, amount=1):
        """
        >>> s._purge()
        >>> s.zincrby_nr('foo', 'bar', 2)
        >>> s.zscore('foo', 'bar')
        2

        >>> s.zincrby_nr('foo', 'bar')
        >>> s.zscore('foo', 'bar')
        3
        """
        self.execute_command(ZIncrByNR(name, amount, value))


def run_tests(deps_provider):
    '''
    '''
    import seneca.engine.storage.redisnap.local_backend as l_back

    c = Client(executer = print)
    s = Client(executer = l_back.Executer())

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
