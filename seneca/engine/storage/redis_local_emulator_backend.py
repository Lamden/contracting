"""
Note: Not threadsafe


"""
from seneca.engine.storage.resp_commands import *


class Executer():
    '''
    Maps command objects to actual Redis commands and runs them, leans heavily
    on redis.py
    '''
    def __init__(self):
        self.data = {}

    def type(self, cmd):
        return type(self.get(Get(cmd.key)))

    def get(self, cmd):
        try:
            ret = self.data[cmd.key]
            assert isinstance(ret, RScalar)
            return ret
        except KeyError:
            return RNoValueExists()

    def set(self, cmd):
        assert isinstance(cmd.value, RScalar)
        self.data[cmd.key] = cmd.value

    def exists(self, cmd):
        return cmd.key in self.data

    def incrby(self, cmd):
        v = self.get(Get(cmd.key))
        assert isinstance(v, RScalarInt)
        v.value += cmd.amount
        self.set(Set(cmd.key, v))
        return v

    def incr(self, cmd):
        return self.incrby(IncrBy(cmd.key, 1))

    def decr(self, cmd):
        return self.incrby(IncrBy(cmd.key, -1))



    def __call__(self, cmd):
        d = self.data

        # TODO: Make sure this is efficient and generally okay.
        return getattr(self, cmd.__class__.__name__.lower())(cmd)


def run_tests(deps_provider):
    '''
    >>> ex(Exists('foo')); ex(Get('foo')); ex(Type('foo'))
    False
    <RESP (RNoValueExists) {}>
    <class 'seneca.engine.storage.resp_types.RNoValueExists'>

    >>> _ = ex(Set('foo', make_rscalar('bar')))
    >>> ex(Exists('foo')); ex(Get('foo')); ex(Type('foo'))
    True
    <RESP (RScalar) {'value': 'bar'}>
    <class 'seneca.engine.storage.resp_types.RScalar'>

    Running set with an Float, value is stored as a RScalarFloat
    >>> ex(Set('foo', make_rscalar(1.0))); ex(Get('foo')); ex(Type('foo'))
    <RESP (RScalarFloat) {'value': 1.0}>
    <class 'seneca.engine.storage.resp_types.RScalarFloat'>

    Running set with a string that looks like a Float, value is STILL stored as
    a RScalarFloat
    >>> ex(Set('foo', make_rscalar('1.0'))); ex(Get('foo')); ex(Type('foo'))
    <RESP (RScalarFloat) {'value': 1.0}>
    <class 'seneca.engine.storage.resp_types.RScalarFloat'>

    Running set with an Int, value is stored as a RScalarInt
    >>> ex(Set('foo', make_rscalar(1))); ex(Get('foo')); ex(Type('foo'))
    <RESP (RScalarInt) {'value': 1}>
    <class 'seneca.engine.storage.resp_types.RScalarInt'>

    Running set with a string that looks like an Int, value is STILL stored as
    a RScalarInt
    >>> ex(Set('foo', make_rscalar('1'))); ex(Get('foo')); ex(Type('foo'))
    <RESP (RScalarInt) {'value': 1}>
    <class 'seneca.engine.storage.resp_types.RScalarInt'>

    >>> ex(Incr('foo'))
    <RESP (RScalarInt) {'value': 2}>

    >>> ex(IncrBy('foo', 10))
    <RESP (RScalarInt) {'value': 12}>





    >> ex(Set('foo', 'bar'))
    SET foo bar
    >> ex(Append('foo', 'bar'))
    APPEND foo bar
    >> ex(Incr('foo'))
    INCRBY foo 1
    >> ex(IncrBy('foo', 3))
    INCRBY foo 3
    >> ex(Decr('foo'))
    DECRBY foo 1
    >> ex(DecrBy('foo', 3))
    DECRBY foo 3
    '''
    ex = Executer()

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
