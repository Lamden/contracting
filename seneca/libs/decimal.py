from decimal import Context
from seneca.constants.env import DECIMAL_PRECISION


def make_decimal(f):
    return Context(prec=DECIMAL_PRECISION).create_decimal_from_float(f)