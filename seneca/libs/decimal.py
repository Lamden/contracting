from decimal import Context, getcontext, Decimal
from seneca.constants.env import DECIMAL_PRECISION

getcontext().prec = DECIMAL_PRECISION


def make_decimal(f):
    f = str(f)
    return Decimal(f)
