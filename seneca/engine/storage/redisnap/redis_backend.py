'''
Some code for GetExactType, or better, use Lua
'''
import redis
from seneca.engine.storage.redisnap.commands import *


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
            Type: lambda c: r.type(c.addr),
            Exists: lambda c: r.exists(c.addr),
            Get: lambda c: r.get(c.addr),
            Set: lambda c: r.set(c.addr, c.value),
            Append: lambda c: r.append(c.addr, c.value),
            IncrBy: lambda c: r.incr(c.addr, c.amount),
        }

        return converters[type(cmd)](cmd)


def run_tests(deps_provider):
    '''
    '''

    import doctest, sys

    def just_print(_, *args):
        print(*args)

    # Monkey patch redis-py, just print commands instead of trying to run them.
    redis.StrictRedis.execute_command = just_print
    ex = Executer()

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
