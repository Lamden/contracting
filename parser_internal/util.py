from functools import wraps
from inspect import signature, _empty

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


def fst(tup):
    return(tup[0])

def snd(tup):
    return(tup[1])

def swap(tup):
    x, y = tup
    return y, x


def f_apply(f,x):
    return f(x)


def compose(f,g):
    return lambda x: f(g(x))

def intercalate(x, ys):
    '''Like join, but filters Falsey values'''
    return x.join([x for x in ys if x])
