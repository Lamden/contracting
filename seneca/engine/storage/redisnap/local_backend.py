"""
Note: Not threadsafe

This Redisnap backend stores data in Python objects. It can be used as a
standalone backend, but it's primarily designed to be used inside the
transactional backend.

TODO: Convert camelcase to snake.
TODO: Add type annotations to everything.
TODO: If there are enough type check of existing values, just change to
decorator.

TODO: Custom exception types, important!

"""
from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.resp_types as rtype
#from seneca.engine.storage.redisnap.addresses import *

class Executer():
    '''
    Maps command objects to actual Redis commands and runs them, leans heavily
    on redis.py

    TODO: We should efficiently track collisions and decide whether we want to
    use a log of transactions to commit, or create ops from the stored data
    '''
    def __init__(self):
        self.data = {}
        self.log =[]

    def purge(self):
        self.data = {}

    def exists(self, cmd):
        '''
        >>> _ = ex.purge()
        >>> ex(Exists('foo'));
        False
        '''
        return cmd.key in self.data

    def type(self, cmd):
        """
        >>> _ = ex.purge()
        >>> t = ex(Type('foo'))
        >>> print(t.__name__)
        RDoesNotExist
        >>> issubclass(t, RScalar)
        True
        """
        return type(self.get(Get(cmd.key)))

    def get(self, cmd):
        """
        >>> _ = ex.purge()
        >>> ex(Get('foo'))
        RDoesNotExist()
        """
        try:
            ret = self.data[cmd.key]
            assert isinstance(ret, RScalar), 'FSR we got the wrong type!'
            return ret
        except KeyError:
            return RDoesNotExist()

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
        'RScalarInt'
        RScalarInt(1)
        """
        self.data[cmd.key] = make_rscalar(cmd.value)



    def incrbywo(self, cmd):
        #TODO: Change name to incrby_wo()
        '''
        >>> ex.purge()

        Increment an empty key
        >>> ex(IncrByWo('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(1)

        Increment an existing key
        >>> ex(IncrByWo('foo', 1));

        >>> ex(Get('foo'))
        RScalarInt(2)

        Incremenent non-int scalars
        >>> ex(Set('foo', 'bar'))
        >>> exception_to_string(ex, IncrByWo('foo', 1))
        'Existing value has wrong type.'

        >>> ex(Set('foo', 1.0))
        >>> exception_to_string(ex, IncrByWo('foo', 1))
        'Existing value has wrong type.'

        TODO: Increment non-scalar
        '''
        old = self(Get(cmd.key))
        old_type = type(old)

        if issubclass(old_type, RDoesNotExist):
            self(Set(cmd.key, cmd.amount))
        elif issubclass(old_type, RScalarInt):
            old.value += cmd.amount
        else:
            raise Exception('Existing value has wrong type.')

    def hget(self, cmd):
        """
        >>> ex.purge()
        >>> ex(HGet('foo', 'bar'))
        RDoesNotExist()
        """
        try:
            maybe_rhash = self.data[cmd.key]
            if isinstance(maybe_rhash, RHash):
                return maybe_rhash.value[cmd.field]
            else:
                raise Exception('Existing value has wrong type.')
        except KeyError:
            return RDoesNotExist()


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
        if cmd.key in self.data:
            old_val = self.data[cmd.key]
            if not isinstance(old_val, RHash):
                raise Exception('Existing value has wrong type.')
            else:
                inner_dict = self.data[cmd.key].value
                inner_dict[cmd.field] = make_rscalar(cmd.value)
        else:
            self.data[cmd.key] = RHash({cmd.field: make_rscalar(cmd.value)})


    def __call__(self, cmd):
        # TODO: Make sure this is efficient and generally okay.
        return getattr(self, cmd.__class__.__name__.lower())(cmd)


def run_tests(deps_provider):
    ex = Executer()

    def exception_to_string(*args):
        try:
            return args[0](*args[1:])
        except Exception as e:
            return str(e)

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
