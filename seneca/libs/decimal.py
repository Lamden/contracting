from decimal import Context


def make_decimal(f):
    return Context(prec=2).create_decimal_from_float(f)