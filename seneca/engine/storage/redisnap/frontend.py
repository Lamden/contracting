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

#   TODO: Implement in localbackend and here.
#   def append_wo(self, key, value):
#       """
#       Appends the string ``value`` to the value at ``key``. If ``key``
#       doesn't already exist, create it with a value of ``value``.
#       Returns the new length of the value at ``key``.
#
#       >>> s.append('foo', 'bar')
#
#       """
#       return self.execute_command(Append(key, value))

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

    def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        >>> s.set('foo', 'bar'); s.get('foo')
        b'bar'

        >>> s.set('foo', 'baz'); s.get('foo')
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

        self.execute_command(Set(name, value))


    def __setitem__(self, name, value):
        """
        >> c['foo'] = 'bar'
        """
        self.set(name, value)


    def incr_wo(self, name, amount=1):
        """
        >>> s._purge() is None
        True

        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> s.incr_wo('foo', 1) is None
        True
        """
        self.execute_command(IncrByWO(name, amount))


    def incrby_wo(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> s.incrby_wo('foo', 1) is None
        True
        """
        self.execute_command(IncrByWO(name, amount))

    def decr_wo(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        >>> s.decr_wo('foo', 1) is None
        True
        """
        self.execute_command(IncrByWO(name, 0 - amount))

    def hget(self, name, key):
        """
        >>> s.hget('foo', 'bar') is None
        True
        """
        ret = self.execute_command(HGet(name, key))
        if isinstance(ret, RDoesNotExist):
            return None
        elif isinstance(ret, RScalar):
            return ret.to_bytes()

    def hset_wo(self, name, key, value):
        """
        >>> s.hset_wo('foo', 'bar', 'baz'); s.hget('foo', 'bar')
        b'baz'
        """
        self.execute_command(HSet(name, key, value))


def run_tests(deps_provider):
    '''
    '''
    import seneca.engine.storage.redisnap.local_backend as lb

    c = Client(executer = print)
    s = Client(executer = lb.Executer())

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
