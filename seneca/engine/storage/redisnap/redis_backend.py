"""
"""
import redis

from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.resp_types as rtype
#from seneca.engine.storage.redisnap.addresses import *

def bytes_to_rscalar(b):
    if b:
        b = b.decode("utf-8")
    return rtype.make_rscalar(b)


class Executer():
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
        """
        >>> _ = ex.purge()
        >>> ex(Exists('foo'));
        False
        """
        return self._redis_executer.exists(cmd.key)

    def type(self, cmd):
        """
        >>> _ = ex.purge()
        >>> t = ex(Type('foo'))
        >>> print(t.__name__)
        RDoesNotExist
        >>> issubclass(t, RScalar)
        True
        """
        return rtype.from_resp_str(self._redis_executer.type(cmd.key).decode("utf-8"))

    def asserttype(self, cmd):
        """
        >>> ex.purge()
        >>> ex(Set('foo', 'bar'))
        >>> ex(AssertType('foo', RScalar))
        True
        >>> ex(AssertType('foo', RHash))
        False

        NOTE: This is the exact same implementation in local and redis backends
        """
        return isinstance(self.get(cmd), cmd.r_type)

    def get(self, cmd):
        """
        >> _ = ex.purge()
        >> ex(Get('foo'))
        RDoesNotExist()
        """
        return bytes_to_rscalar(self._redis_executer.get(cmd.key))


    def set(self, cmd):
        """
        >>> _ = ex.purge()
        >>> ex(Set('foo', 'bar'))

        >>> ex(Exists('foo'))
        True

        >>> ex(Type('foo')).__name__; ex(Get('foo'))
        'RScalar'
        RScalar('bar')

        >>> _ = ex(Set('foo', 1)); ex(Type('foo')).__name__; ex(Get('foo'))
        'RScalar'
        RScalarInt(1)
        """
        self._redis_executer.set(cmd.key, cmd.value)

    def incrbywo(self, cmd):
        #TODO: Change name to incrby_wo()
        """
        >>> ex.purge()

        Increment an empty key
        >>> ex(IncrByWO('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(1)

        Increment an existing key
        >>> ex(IncrByWO('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(2)

        Incremenent non-int scalars
        >>> ex(Set('foo', 'bar'))

        >>> exception_to_string(ex, IncrByWO('foo', 1))
        'Existing value has wrong type.'

        >>> ex(Set('foo', 1.0))
        >>> exception_to_string(ex, IncrByWO('foo', 1))
        'Existing value has wrong type.'
        """
        try:
            self._redis_executer.incr(cmd.key, cmd.amount)
        except redis.exceptions.ResponseError as e:
            if str(e) == 'value is not an integer or out of range':
                raise Exception('Existing value has wrong type.')
            else:
                raise

    def appendwo(self, cmd):
        """
        >>> ex.purge()
        >>> ex(AppendWO('foo', 'abc')); ex(Get('foo'))
        RScalar('abc')
        >>> ex(AppendWO('foo', 'abc')); ex(Get('foo'))
        RScalar('abcabc')

        >>> ex(AppendWO('fooint', '1')); ex(Get('fooint'))
        RScalarInt(1)
        >>> ex(AppendWO('fooint', '1')); ex(Get('fooint'))
        RScalarInt(11)
        """
        self._redis_executer.append(cmd.key, cmd.value)


    def hget(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HGet('foo', 'bar'))
        RDoesNotExist()
        """
        return bytes_to_rscalar(self._redis_executer.hget(cmd.key, cmd.field))

    def hset(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HSet('foo', 'bar', 'baz'))
        >>> ex(HGet('foo', 'bar'))
        RScalar('baz')

        >>> ex(HSet('foo', 'bar', 1))
        >>> ex(HGet('foo', 'bar'))
        RScalarInt(1)
        """
        self._redis_executer.hset(cmd.key, cmd.field, cmd.value)

    def del_(self, cmd):
        self._redis_executer.delete(cmd.key)


    def lindex(self, cmd):
        """
        >>> ex.purge()

        >>> ex(RPushNR('foo', ['bar']))
        >>> ex(LIndex('foo', 0))
        RScalar('bar')

        >>> ex(LIndex('foo', 20))
        RDoesNotExist()

        >>> ex.purge()

        >>> ex(LIndex('foo', 0))
        RDoesNotExist()

        >>> ex(Set('foo', 'bar'))
        >>> e = return_exception(ex, LIndex('foo', 0))
        >>> type(e).__name__; str(e)
        'RedisKeyTypeError'
        'Existing value has wrong type.'
        """
        try:
            return bytes_to_rscalar(self._redis_executer.lindex(cmd.key, cmd.index))
        except redis.exceptions.ResponseError as e:
            if e.args[0] == 'WRONGTYPE Operation against a key holding the wrong kind of value':
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                raise


    def lset(self, cmd):
        """
        >>> ex.purge()
        >>> e = return_exception(ex, LSet('foo', 0, 'bar'))
        >>> str(e)
        'Cannot LSet an nonexistent key.'

        >>> ex(RPushNR('foo', ['bar']))
        >>> ex(LSet('foo', 0, 'baz'))

        >>> e = return_exception(ex, LSet('foo', 1, 'bar'))
        >>> type(e).__name__; str(e);
        'RedisKeyTypeError'
        'Index out of range.'
        """
        try:
            self._redis_executer.lset(cmd.key, cmd.index, cmd.value)
        except redis.exceptions.ResponseError as e:
            if e.args[0] == 'no such key':
                raise RedisKeyTypeError('Cannot LSet an nonexistent key.')
            elif e.args[0] == 'index out of range':
                return RedisKeyTypeError('Index out of range.')
            else:
                raise


    def lpushnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(LPushNR('foo', ['bar']))
        """
        self._redis_executer.lpush(cmd.key, *cmd.value)


    def rpushnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(RPushNR('foo', ['bar']))
        """
        self._redis_executer.rpush(cmd.key, *cmd.value)


    def _pop_base(self, method_name, cmd):
        try:
            return bytes_to_rscalar(getattr(self._redis_executer, method_name)(cmd.key))
        except redis.exceptions.ResponseError as e:
            if e.args[0] == 'WRONGTYPE Operation against a key holding the wrong kind of value':
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                raise


    def lpop(self, cmd):
        """
        >>> ex.purge()
        >>> ex(LPop('foo'))
        RDoesNotExist()

        >>> ex(Set('foo', 'bar'))
        >>> exception_type_name(ex, LPop('foo'))
        'RedisKeyTypeError'

        >>> ex.purge()
        >>> ex(LPushNR('foo', ['bar', 'baz']))
        >>> ex(LPop('foo')); ex(LPop('foo'))
        RScalar('baz')
        RScalar('bar')
        """
        return self._pop_base('lpop', cmd)


    def rpop(self, cmd):
        """
        >>> ex.purge()
        >>> ex(RPushNR('foo', ['bar', 'baz']))
        >>> ex(RPop('foo')); ex(RPop('foo'))
        RScalar('baz')
        RScalar('bar')
        """
        return self._pop_base('rpop', cmd)


    def __call__(self, cmd):
        # TODO: Make sure this is efficient and generally okay.

        if isinstance(cmd, Del):
            self.del_(cmd)
        else:
            return getattr(self, cmd.__class__.__name__.lower())(cmd)


def run_tests(deps_provider):
    ex = Executer(host='127.0.0.1', port=32768)

    def exception_to_string(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return str(e)

    def exception_type_name(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return type(e).__name__

    def return_exception(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return e


    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
