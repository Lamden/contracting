from functools import wraps
from inspect import signature

def auto_set_fields(f):
    f_sig = signature(f)

    @wraps(f)
    def wrapper(*args, **kwargs):
        fields = dict(f_sig.bind(*args, **kwargs).arguments)
        self = fields.pop('self')

        for k, v in fields.items():
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
