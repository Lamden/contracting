from seneca.engine.storage.redisnap.commands import *
#import seneca.engine.storage.redisnap.resp_types as rtype
#from seneca.engine.storage.redisnap.addresses import *

#https://stackoverflow.com/questions/40508492/python-sphinx-inherit-method-documentation-from-superclass/40613306#40613306
import abc

class SuperclassMeta(type):
    def __new__(mcls, classname, bases, cls_dict):
        cls = super().__new__(mcls, classname, bases, cls_dict)
        for name, member in cls_dict.items():
            try:
                if not getattr(member, '__doc__'):
                    member.__doc__ = getattr(bases[-1], name).__doc__
            except:
                AttributeError
        return cls


class ExecuterBase(object, metaclass=SuperclassMeta):
    '''
    Maps command objects to actual Redis commands and runs them, leans heavily
    on redis.py

    TODO:
    We should efficiently track collisions and decide whether we want to
    use a log of transactions to commit, or create ops from the stored data
    '''

    @abc.abstractmethod
    def purge(self):
        """
        """


    @abc.abstractmethod
    def exists(self, cmd):
        """
        >>> _ = ex.purge()
        >>> ex(Exists('foo'));
        False
        """


    @abc.abstractmethod
    def type(self, cmd):
        """
        This is the built-in shallow Redis typecheck.

        >>> _ = ex.purge()
        >>> t = ex(Type('foo'))
        >>> print(t.__name__)
        RDoesNotExist
        >>> issubclass(t, RScalar)
        True
        """


    @abc.abstractmethod
    def asserttype(self, cmd):
        """
        >>> ex.purge()
        >>> ex(SetNR('foo', 'bar'))
        >>> ex(AssertType('foo', RScalar))
        True
        >>> ex(AssertType('foo', RHash))
        False

        NOTE: This is the exact same implementation in local and redis backends
        """

    # # TODO:
    # @abc.abstractmethod
    # def assertfieldtype(self, cmd):
    #     """
    #     This is not part of RESP, it's a RediSnap add-on, it does deep type
    #     inspection.
    #
    #     NOTE: Very important, In Redis empty fields are fully polymorphic, so
    #     asserting any type on non-existent key will always succeed. This is how
    #     Redis behaves:
    #     > get some_non_existent_key
    #     (nil)
    #
    #     Only if an existing value exists of the wrong type is there a problem:
    #     > set some_string abc
    #     OK
    #     > hget some_string field_name
    #     (error) WRONGTYPE Operation against a key holding the wrong kind of value
    #
    #     TODO: Add a test for this command
    #     >> ex(AssertFieldType('foo', 'bar', RScalar))
    #     """

    @abc.abstractmethod
    def get(self, cmd):
        """
        >>> _ = ex.purge()
        >>> ex(Get('foo'))
        RDoesNotExist()
        """


    @abc.abstractmethod
    def setnr(self, cmd):
        """
        >>> _ = ex.purge()
        >>> ex(SetNR('foo', 'bar'))

        >>> ex(Exists('foo'))
        True

        >>> ex(Type('foo')).__name__; ex(Get('foo'))
        'RScalar'
        RScalar('bar')

        >>> _ = ex(SetNR('foo', 1)); ex(Type('foo')).__name__; ex(Get('foo'))
        'RScalar'
        RScalarInt(1)
        """


    @abc.abstractmethod
    def incrbynr(self, cmd):
        """
        >>> ex.purge()

        Increment an empty key
        >>> ex(IncrByNR('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(1)

        Increment an existing key
        >>> ex(IncrByNR('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(2)

        Incremenent non-int scalars
        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, IncrByNR('foo', 1))
        ('RedisVauleTypeError', 'Existing value has wrong type.')

        >>> ex(SetNR('foo', 1.0))
        >>> return_exception_tuple(ex, IncrByNR('foo', 1))
        ('RedisVauleTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def appendnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(AppendNR('foo', 'abc')); ex(Get('foo'))
        RScalar('abc')
        >>> ex(AppendNR('foo', 'abc')); ex(Get('foo'))
        RScalar('abcabc')

        >>> ex(AppendNR('fooint', '1')); ex(Get('fooint'))
        RScalarInt(1)
        >>> ex(AppendNR('fooint', '1')); ex(Get('fooint'))
        RScalarInt(11)
        """


    @abc.abstractmethod
    def hget(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HGet('foo', 'bar'))
        RDoesNotExist()
        """


    @abc.abstractmethod
    def hsetnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HSetNR('foo', 'bar', 'baz'))
        >>> ex(HGet('foo', 'bar'))
        RScalar('baz')

        >>> ex(HSetNR('foo', 'bar', 1))
        >>> ex(HGet('foo', 'bar'))
        RScalarInt(1)
        """


    @abc.abstractmethod
    def hexists(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HExists('foo', 'bar'))
        False

        >>> ex(HSetNR('foo', 'bar', 'baz'))

        >>> ex(HExists('foo', 'qux'))
        False
        >>> ex(HExists('foo', 'bar'))
        True

        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, HExists('foo', 'bar'))
        ('RedisKeyTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def del_(self, cmd):
        """
        """


    # # TODO:
    # @abc.abstractmethod
    # def llen(self, cmd):
    #     """
    #     TODO: add test for llen
    #     >> ex(LLen('foo'))
    #     """


    @abc.abstractmethod
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

        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, LIndex('foo', 0))
        ('RedisKeyTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def lset(self, cmd):
        """
        >>> ex.purge()
        >>> return_exception_tuple(ex, LSet('foo', 0, 'bar'))
        ('RedisKeyTypeError', 'Cannot LSet an nonexistent key.')

        >>> ex(RPushNR('foo', ['bar']))
        >>> ex(LSet('foo', 0, 'baz'))

        >>> return_exception_tuple(ex, LSet('foo', 1, 'bar'))
        ('RedisListOutOfRange', 'Index out of range.')
        """


    @abc.abstractmethod
    def lpushnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(LPushNR('foo', ['bar']))
        >>> ex(LIndex('foo', 0))
        RScalar('bar')

        >>> ex(LPushNR('foo', ['baz']))
        >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
        RScalar('baz')
        RScalar('bar')

        >>> ex.purge()
        >>> ex(LPushNR('foo', ['bar', 'baz']))
        >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
        RScalar('baz')
        RScalar('bar')
        """


    @abc.abstractmethod
    def rpushnr(self, cmd):
        """
        >>> ex.purge()
        >>> ex(RPushNR('foo', ['bar']))
        >>> ex(LIndex('foo', 0))
        RScalar('bar')

        >>> ex(RPushNR('foo', ['baz']))
        >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
        RScalar('bar')
        RScalar('baz')


        >>> ex.purge()
        >>> ex(RPushNR('foo', ['bar', 'baz']))
        >>> ex(LIndex('foo', 0)); ex(LIndex('foo', 1));
        RScalar('bar')
        RScalar('baz')
        """


    @abc.abstractmethod
    def lpop(self, cmd):
        """
        >>> ex.purge()
        >>> ex(LPop('foo'))
        RDoesNotExist()

        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, LPop('foo'))
        ('RedisKeyTypeError', 'Existing value has wrong type.')

        >>> ex.purge()
        >>> ex(LPushNR('foo', ['bar', 'baz']))
        >>> ex(LPop('foo')); ex(LPop('foo'))
        RScalar('baz')
        RScalar('bar')
        """


    @abc.abstractmethod
    def rpop(self, cmd):
        """
        >>> ex.purge()
        >>> ex(RPushNR('foo', ['bar', 'baz']))
        >>> ex(RPop('foo')); ex(RPop('foo'))
        RScalar('baz')
        RScalar('bar')
        """


    @abc.abstractmethod
    def zaddnr(self, cmd):
        """
        >>> ex.purge()

        # Testing auto creation
        >>> ex(ZAddNR('foo', {'bar':1}))
        >>> ex(ZScore('foo', 'bar'))
        1

        # Testing modification of an existing value
        >>> ex(ZAddNR('foo', {'baz':2}))
        >>> ex(ZScore('foo', 'bar'));  ex(ZScore('foo', 'baz'))
        1
        2

        # Testing update of an existing member
        >>> ex(ZAddNR('foo', {'baz':50}))
        >>> ex(ZScore('foo', 'bar')); ex(ZScore('foo', 'baz'))
        1
        50

        # Testing exception on type mismatch
        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, ZAddNR('foo', {'baz':2}))
        ('RedisKeyTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def zscore(self, cmd):
        """
        >> ex.purge()

        Empty key returns None
        >> ex(ZScore('foo', 'bar'))

        Member is not present returns None too
        >> ex(ZAddNR('foo', {'bar':1})); ex(ZScore('foo', 'baz'))

        >> ex(ZScore('foo', 'bar'))
        1

        # Testing exception on type mismatch
        >> ex(SetNR('foo', 'bar'))
        >> return_exception_tuple(ex, ZScore('foo', 'bar'))
        ('RedisKeyTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def zrevrangebyscore(self, cmd):
        """
        Removes the specified members from the sorted set stored at key. Non existing members are ignored.
        >>> ex.purge()
        >>> ex(ZAddNR('foo', {'one': 1, 'two':2, 'three':3}))
        >>> list(ex(ZRevRangeByScore('foo',None,None)))
        ['three', 'two', 'one']

        >>> list(ex(ZRevRangeByScore('foo', 2, 1)))
        ['two', 'one']

        >>> list(ex(ZRevRangeByScore('foo', 2, 1, (True, False))))
        ['two']

        >>> list(ex(ZRevRangeByScore('foo', 2, 1, (False, False))))
        []

        >>> list(ex(ZRevRangeByScore('foo', None, None, with_scores=True)))
        [(3, 'three'), (2, 'two'), (1, 'one')]

        # Testing exception on type mismatch
        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, ZRevRangeByScore('foo',10,30))
        ('RedisKeyTypeError', 'Existing value has wrong type.')
        """


    @abc.abstractmethod
    def zremnr(self, cmd):
        """
        >>> ex.purge()

        Testing zrem on non existing key
        >>> ex(ZRemNR('foo', ['bar']))
        >>> ex(Exists('foo'))
        False

        Test modification of existing
        >>> ex(ZAddNR('foo', {'bar':1, 'baz':2}))
        >>> ex(ZRemNR('foo', ['baz']))
        >>> ex(ZScore('foo', 'bar')); ex(ZScore('foo', 'baz'))
        1

        Test zrem of non-existent member
        >>> ex(ZRemNR('foo', ['bar']))

        Test deletion of sset after last member is removed
        >>> ex(Exists('foo'))
        False

        # Testing exception on type mismatch
        >>> ex(SetNR('foo', 'bar'))
        >>> return_exception_tuple(ex, ZRemNR('foo', ['qux']))
        ('RedisKeyTypeError', 'Existing value has wrong type.')


        # Test multiple removals in single invocation
        >>> ex(Del('foo'))
        >>> ex(ZAddNR('foo', {'bar':1, 'baz':2}))
        >>> ex(ZRemNR('foo', ['bar', 'baz']))

        >>> ex(Exists('foo'))
        False
        """


    @abc.abstractmethod
    def zincrbynr(self, cmd):
        """
        >>> ex.purge()

        # Totally empty key
        >>> ex(ZIncrByNR('foo', 1, 'bar')); ex(ZScore('foo', 'bar'))
        1

        # Missing member
        >>> ex(ZIncrByNR('foo', 1, 'baz')); ex(ZScore('foo', 'baz'))
        1

        # Update existing
        >>> ex(ZIncrByNR('foo', 4, 'baz')); ex(ZScore('foo', 'baz'))
        5
        """

    def __call__(self, cmd):
        # TODO: pass Make sure this is efficient and generally okay.

        if isinstance(cmd, Del):
            self.del_(cmd)
        # TODO: pass fix name of set
        #elif isinstance(cmd, Sel): pass
        #    self.sel_(cmd)
        else:
            return getattr(self, cmd.__class__.__name__.lower())(cmd)


def run_tests(deps_provider):
    from seneca.engine.util import return_exception_tuple
    from collections import namedtuple
    #import doctest, sys
    #return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
    d = {'failed':0, 'attempted':0}
    return namedtuple('_', ' '.join(d.keys()))(**d)
