'''
This module is a redis-py compatible library.
* Unlike redis-py, the backend is configurable, it could write to a Redis, it
  could save the data locally.
* It generates resp command objects that are run by the backend
'''

from seneca.engine.storage.redisnap.commands import *

class Client:
    '''
    Implementation of the API provided by redis-py's StrictRedis
    '''

    def __init__(self, executer):
        self.execute_command = executer

    def exists(self, name):
        """
        Returns a boolean indicating whether key ``name`` exists
        >>> c.exists('foo')
        <RESP (Exists) {'addr': 'foo'}>
        """
        return self.execute_command(Exists(name))
    __contains__ = exists


    def type(self, name):
        """
        Returns the type of key ``name``
        >>> c.type('foo')
        <RESP (Type) {'addr': 'foo'}>
        """
        return self.execute_command(Type(name))


    def append(self, key, value):
        """
        Appends the string ``value`` to the value at ``key``. If ``key``
        doesn't already exist, create it with a value of ``value``.
        Returns the new length of the value at ``key``.

        >>> c.append('foo', 'bar')
        <RESP (Append) {'addr': 'foo', 'value': 'bar'}>
        """
        return self.execute_command(Append(key, value))


    def get(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        >>> c.get('foo')
        <RESP (Get) {'addr': 'foo'}>
        """
        # TODO: Decide how we want to handle non-existing keys in the commands api
        return self.execute_command(Get(name))

    def __getitem__(self, name):
        """
        Return the value at key ``name``, raises a KeyError if the key
        doesn't exist.

        >>> try:
        ...     c['foo']
        ... except Exception as e:
        ...     print(e)
        <RESP (Get) {'addr': 'foo'}>
        'foo'
        """
        value = self.get(name)
        if value is not None:
            return value
        raise KeyError(name)

    def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        """
        >>> c.set('foo', 'bar')
        <RESP (Set) {'addr': <RESP ADDRESS (ScalarAddress) {'key': 'foo'}>, 'value': 'bar'}>

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

        return self.execute_command(Set(ScalarAddress(name), value))


    def __setitem__(self, name, value):
        """
        >>> c['foo'] = 'bar'
        <RESP (Set) {'addr': <RESP ADDRESS (ScalarAddress) {'key': 'foo'}>, 'value': 'bar'}>
        """
        self.set(name, value)


    def incr(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        >>> c.incr('foo', 1)
        <RESP (IncrBy) {'addr': <RESP ADDRESS (ScalarAddress) {'key': 'foo'}>, 'amount': 1}>



        """
        return self.execute_command(IncrBy(ScalarAddress(name), amount))


    def incrby(self, name, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``


        >>> s.incrby('foo', 1)
        1

        >> s.incrby('foo', 1)
        2
        >> s.set('foo', 1)



        """
        return self.execute_command(IncrBy(ScalarAddress(name), amount))

    def decr(self, name, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        >>> c.decr('foo', 1)
        <RESP (IncrBy) {'addr': 'foo', 'amount': -1}>
        """
        return self.execute_command(IncrBy(name, 0 - amount))


def run_tests(deps_provider):
    '''
    '''
    import seneca.engine.storage.redisnap.local_backend as lb

    c = Client(executer = print)
    s = Client(executer = lb.Executer())

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
