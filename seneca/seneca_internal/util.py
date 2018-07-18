from functools import wraps
from inspect import signature, _empty
from collections import namedtuple
import ast

def auto_set_fields(f):
    f_sig = signature(f)

    @wraps(f)
    def wrapper(*args, **kwargs):
        caller_specified_fields = dict(f_sig.bind(*args, **kwargs).arguments)
        self = caller_specified_fields.pop('self')

        f_defaults = {k: v.default for k, v in \
                       signature(f).parameters.items() \
                       if not v.default is _empty}

        f_defaults.update(caller_specified_fields)
        # Set default values
        for k, v in f_defaults.items():
            setattr(self, k, v)

        return f(*args, **kwargs)

    return wrapper


def run_super_first(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        super_f = getattr(super(type(self), self), f.__name__)
        super_f(*args, **kwargs)
        return f(self)

    return wrapper


def fst(tup):
    '''
    >>> fst((1,2))
    1
    '''
    return(tup[0])


def snd(tup):
    '''
    >>> snd((1,2))
    2
    '''
    return(tup[1])


def swap(tup):
    '''
    >>> swap((1,2))
    (2, 1)
    '''
    x, y = tup
    return y, x


def f_apply(f,x):
    '''
    >>> f_apply(lambda x:x, 1)
    1
    '''
    return f(x)


def assert_len(l, xs):
    # TODO: custom exception classes
    assert len(xs) == l, "List did not have the expected number of items!"
    return xs


def compose(f,g):
    return lambda x: f(g(x))


def intercalate(x, ys):
    '''
    Like join, but filters Falsey values.

    >>> intercalate('_', 'abcde')
    'a_b_c_d_e'
    >>> intercalate('_', [None, 'a', None, 'b'])
    'a_b'
    '''
    return x.join([x for x in ys if x])


#NOTE: This is a decorator function, not a class!
class add_methods(object):
    '''Add the public attributes of a mixin to another class.
    Attribute name collisions result in a TypeError if force is False.
    If a mixin is an ABC, the decorated class is registered to it,
    indicating that the class implements the mixin's interface.

    >>> def id_(self, x):
    ...     return x
    >>> @add_methods(id_)
    ... class Test(object):
    ...     pass
    >>> t = Test()
    >>> t.id_('abc')
    'abc'
    '''
    @auto_set_fields
    def __init__(self, *attrs):
        pass

    def __call__(self, cls):
        for attr in self.attrs:
            if hasattr(cls, attr.__name__):
                raise TypeError("name collision ({})".format(attr.__name__))
            else:
                setattr(cls, attr.__name__, attr)

        return cls


#NOTE: This is a decorator function, not a class!
class add_method_as(object):
    '''
    Add the public attributes of a mixin to another class.
    Attribute name collisions result in a TypeError if force is False.
    If a mixin is an ABC, the decorated class is registered to it,
    indicating that the class implements the mixin's interface.

    >>> def id_(self, x):
    ...     return x
    >>> @add_method_as(id_, 'id_')
    ... class Test(object):
    ...     pass
    >>> t = Test()
    >>> t.id_('abc')
    'abc'
    '''
    @auto_set_fields
    def __init__(self, attr, as_name):
        pass

    def __call__(self, cls):
        if hasattr(cls, self.as_name):
            print(dir(cls))
            raise TypeError("name collision ({})".format(self.as_name))
        else:
            setattr(cls, self.as_name, self.attr)

        return cls


def filter_split(f, l):
    '''
    >>> filter_split(lambda x: x == 'x', 'aaxbbxccxddx')
    (['x', 'x', 'x', 'x'], ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd'])
    '''
    accepted = []
    rejected = []
    [accepted.append(x) if f(x) else rejected.append(x) for x in l]
    return (accepted, rejected)


def dict_to_nt(d, typename='seneca_generate_type'):
    '''
    >>> dict_to_nt({'x':'y'})
    seneca_generate_type(x='y')
    '''
    return namedtuple(typename, d.keys())(*d.values())


def dict_to_obj(d, typename=None):
    '''
    >>> dict_to_obj({'x': 'y'}).x
    'y'
    '''
    empty = lambda: None

    for k,v in d.items():
        setattr(empty, k, v)

    return empty


def manual_import(path, name):
    '''Should work pretty similar to built-in import, but...
    * Not a singleton
    * Doesn't bind to scope, just returns value
    * TODO:What else???

    >>> m = manual_import(__file__, 'tester')
    >>> type(m)
    <class 'dict'>
    >>> 'manual_import' in m.keys()
    True

    TODO: More tests.
    '''
    with open(path, 'r') as file:
        module_string = file.read()

    mod_dict = {'__file__': path, '__name__': name}
    mod_ast = ast.parse(module_string)
    mod_comp = compile(mod_ast, filename=name, mode="exec")
    exec(mod_comp, mod_dict)

    return mod_dict


def run_tests():
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
