from decimal import Context


def make_decimal(f):
    print('hello')
    return Context(prec=2).create_decimal_from_float(f)