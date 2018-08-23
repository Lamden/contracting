'''
Some code for GetExactType, or better, use Lua


'''
import redis
from seneca.engine.storage.resp_commands import *


class Executer():
    '''
    Maps command objects to actual Redis commands and runs them, leans heavily
    on redis.py
    '''
    def __init__(self, *args, **kwargs):
        self.redis = redis.StrictRedis(*args, **kwargs)

    def __call__(self, cmd):
        r = self.redis

        converters = {
            Type: lambda c: r.type(c.key),
            Exists: lambda c: r.exists(c.key),
            Get: lambda c: r.get(c.key),
            Set: lambda c: r.set(c.key, c.value),
            Append: lambda c: r.append(c.key, c.value),
            Incr: lambda c: r.incr(c.key, 1),
            Decr: lambda c: r.decr(c.key, 1),
            IncrBy: lambda c: r.incr(c.key, c.amount),
            DecrBy: lambda c: r.decr(c.key, c.amount),
        }

        return converters[type(cmd)](cmd)


def run_tests(deps_provider):
    '''
    >>> ex(Get('foo'))
    GET foo
    >>> ex(Exists('foo'))
    EXISTS foo
    >>> ex(Type('foo'))
    TYPE foo
    >>> ex(Set('foo', 'bar'))
    SET foo bar
    >>> ex(Append('foo', 'bar'))
    APPEND foo bar
    >>> ex(Incr('foo'))
    INCRBY foo 1
    >>> ex(IncrBy('foo', 3))
    INCRBY foo 3
    >>> ex(Decr('foo'))
    DECRBY foo 1
    >>> ex(DecrBy('foo', 3))
    DECRBY foo 3
    '''

    import doctest, sys

    def just_print(_, *args):
        print(*args)

    # Monkey patch redis-py, just print commands instead of trying to run them.
    redis.StrictRedis.execute_command = just_print
    ex = Executer()

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
