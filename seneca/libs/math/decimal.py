from decimal import getcontext, Decimal
from seneca.config import DECIMAL_PRECISION

getcontext().prec = DECIMAL_PRECISION


def to_decimal(f):
    f = str(f)
    return Decimal(f)
