"""
"""
import redis
from functools import wraps
from seneca.engine.util import grouper

from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.resp_types as rtype
#from seneca.engine.storage.redisnap.addresses import *
from seneca.engine.storage.redisnap.backend_abc import ExecuterBase as abc_executer

def bytes_to_rscalar(b):
    if b:
        b = b.decode("utf-8")
    return rtype.make_rscalar(b)


class Executer(abc_executer):
    '''
    Maps command objects to actual Redis commands and runs them, leans heavily
    on redis.py

    TODO: We should efficiently track collisions and decide whether we want to
    use a log of transactions to commit, or create ops from the stored data
    '''
    def __init__(self, host, port):
        self._redis_executer = redis.StrictRedis(host=host, port=port)

    # TODO: decide if this is worth implemeneting
    def purge(self):
       self._redis_executer.flushdb()

    def exists(self, cmd):
        return self._redis_executer.exists(cmd.key)

    def type(self, cmd):
        return rtype.from_resp_str(self._redis_executer.type(cmd.key).decode("utf-8"))

    def asserttype(self, cmd):
        return isinstance(self.get(cmd), cmd.r_type)

    def get(self, cmd):
        return bytes_to_rscalar(self._redis_executer.get(cmd.key))


    def setnr(self, cmd):
        self._redis_executer.set(cmd.key, cmd.value)

    def incrbynr(self, cmd):
        try:
            self._redis_executer.incr(cmd.key, cmd.amount)
        except redis.exceptions.ResponseError as e:
            if str(e) == 'value is not an integer or out of range':
                raise RedisVauleTypeError('Existing value has wrong type.')
            else:
                raise

    def appendnr(self, cmd):
        self._redis_executer.append(cmd.key, cmd.value)


    def hget(self, cmd):
        return bytes_to_rscalar(self._redis_executer.hget(cmd.key, cmd.field))

    def hsetnr(self, cmd):
        self._redis_executer.hset(cmd.key, cmd.field, cmd.value)

    def hexists(self, cmd):
        return self._redis_executer.hexists(cmd.key, cmd.field)

    def del_(self, cmd):
        self._redis_executer.delete(cmd.key)


    def lindex(self, cmd):
        return bytes_to_rscalar(self._redis_executer.lindex(cmd.key, cmd.index))


    def lset(self, cmd):
        try:
            self._redis_executer.lset(cmd.key, cmd.index, cmd.value)
        except redis.exceptions.ResponseError as e:
            if e.args[0] == 'no such key':
                raise RedisKeyTypeError('Cannot LSet an nonexistent key.')
            elif e.args[0] == 'index out of range':
                return RedisListOutOfRange('Index out of range.')
            else:
                raise


    def lpushnr(self, cmd):
        self._redis_executer.lpush(cmd.key, *cmd.value)


    def rpushnr(self, cmd):
        self._redis_executer.rpush(cmd.key, *cmd.value)


    def _pop_base(self, method_name, cmd):
        return bytes_to_rscalar(getattr(self._redis_executer, method_name)(cmd.key))

    def lpop(self, cmd):
        return self._pop_base('lpop', cmd)

    def rpop(self, cmd):
        return self._pop_base('rpop', cmd)

    def zaddnr(self, cmd):
        self._redis_executer.zadd(cmd.key, **cmd.members_and_scores)

    def zscore(self, cmd):
        ret = self._redis_executer.zscore(cmd.key, cmd.member)
        try:
            return int(ret)
        except TypeError:
            return None

    def zrevrangebyscore(self, cmd):
        # redis> ZREVRANGEBYSCORE myzset +inf -inf
        # 1) "three"
        # 2) "two"
        # 3) "one"
        # redis> ZREVRANGEBYSCORE myzset 2 1
        # 1) "two"
        # 2) "one"
        # redis> ZREVRANGEBYSCORE myzset 2 (1
        # 1) "two"
        # redis> ZREVRANGEBYSCORE myzset (2 (1
        def format_redis_range_str(x: int, default: str, marked_inclusive: bool):
            if x is None:
                return default
            else:
                s = str(x)
                if marked_inclusive:
                    return s
                else:
                    return '(' + s

        cmd_parts = [ 'ZREVRANGEBYSCORE',
                      cmd.key,
                      format_redis_range_str(cmd.max, 'inf', cmd.inclusive[0]),
                      format_redis_range_str(cmd.min, '-inf', cmd.inclusive[1]),
            ]

        if cmd.with_scores:
            cmd_parts.append('WITHSCORES')

        full_cmd_str = ' '.join(cmd_parts)
        res = self._redis_executer.execute_command(full_cmd_str)

        if not cmd.with_scores:
            return list(map(lambda x: x.decode('utf-8'), res))
        else:
            res_byte_pairs = grouper(res, 2)
            return map(lambda x_y: ( int(x_y[1]), x_y[0].decode("utf-8") ), res_byte_pairs)


    def zremnr(self, cmd):
        self._redis_executer.zrem(cmd.key, *cmd.members)


    def zincrbynr(self, cmd):
        self._redis_executer.zincrby(cmd.key, cmd.member, cmd.amount)


    def transform_exception(f):
        @wraps(f)
        def wrapper(self, cmd):
            try:
                return f(self, cmd)
            except redis.exceptions.ResponseError as e:
                if e.args[0] == 'WRONGTYPE Operation against a key holding the wrong kind of value':
                    raise RedisKeyTypeError('Existing value has wrong type.')
                else:
                    raise

        return wrapper

    @transform_exception
    def __call__(self, cmd):
        # TODO: Make sure this is efficient and generally okay.

        if isinstance(cmd, Del):
            self.del_(cmd)
        else:
            return getattr(self, cmd.__class__.__name__.lower())(cmd)


def run_tests(deps_provider):
    ex = Executer(host='127.0.0.1', port=32768)
    from seneca.engine.util import return_exception_tuple
    import doctest, sys

    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
