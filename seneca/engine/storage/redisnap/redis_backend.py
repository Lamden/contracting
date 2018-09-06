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

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
