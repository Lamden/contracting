from decimal import Context, getcontext, Decimal
from seneca.constants.config import DECIMAL_PRECISION

getcontext().prec = DECIMAL_PRECISION


def to_decimal(f):
    f = str(f)
    return Decimal(f)
