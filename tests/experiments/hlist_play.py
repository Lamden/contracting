# from seneca.libs.datatypes import *

# thicc_list = hlist(prefix='thicc', value_type=hlist(value_type=str))
#
# thicc_list.push()
import functools

def print_that(this, optional_arg='butt'):
    print("[print_that] this: {} ... that: {} ... with optional arg {}".format(this, that, optional_arg))

# def do_that(key, *args, **kwargs):
#     print("do that called with key {}, args {}, kwargs {}".format(key, args, kwargs))
#     print_that(key, *args, **kwargs)


# do_that('hi')
f = functools.partial(print_that, this='i called this now')
f('i added that later')