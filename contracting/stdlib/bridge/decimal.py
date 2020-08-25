from decimal import Decimal
import decimal

from fpbinary import FpBinary

MAX_BITS_REAL = 256
MAX_BITS_FRAC = 256


def fixed(x):
    if type(x) == FpBinary:
        return x

    d = Decimal(x)
    return FpBinary(int_bits=MAX_BITS_REAL, frac_bits=MAX_BITS_FRAC, signed=True, value=d)


def _fixed(x):
    return FpBinary(int_bits=MAX_BITS_REAL, frac_bits=MAX_BITS_FRAC, signed=True, value=x)


CONTEXT = decimal.Context(prec=16, rounding=decimal.ROUND_FLOOR, Emin=-100, Emax=100)
# There is a much better way to do this...

MAX_DECIMAL = 16


class ContractingDecimal:
    def _get_other(self, other):
        if type(other) == ContractingDecimal:
            return other._d
        elif type(other) == float or type(other) == Decimal:
            return fixed(str(other))

        return other

    def __init__(self, a):
        if type(a) == float:
            a = str(a)

        self._d = fixed(a)

    def __bool__(self):
        if self._d > 0:
            return True
        return False

    def __eq__(self, other):
        return self._d.__eq__(self._get_other(other))

    def __lt__(self, other):
        return self._d.__lt__(self._get_other(other))

    def __le__(self, other):
        return self._d.__le__(self._get_other(other))

    def __gt__(self, other):
        return self._d.__gt__(self._get_other(other))

    def __ge__(self, other):
        return self._d.__ge__(self._get_other(other))

    def __str__(self):
        return self._d.str_ex()

    def __neg__(self):
        return self._d.__neg__()

    def __pos__(self):
        return self._d

    def __abs__(self):
        return self._d.__abs__()

    def __add__(self, other):
        return self._d.__add__(self._get_other(other))

    def __radd__(self, other):
        return self._d.__radd__(self._get_other(other))

    def __sub__(self, other):
        return self._d.__sub__(self._get_other(other))

    def __rsub__(self, other):
        return self._d.__rsub__(self._get_other(other))

    def __mul__(self, other):
        return self._d.__mul__(self._get_other(other))

    def __rmul__(self, other):
        return self._d.__rmul__(self._get_other(other))

    def __truediv__(self, other):
        return self._d.__truediv__(self._get_other(other))

    def __rtruediv__(self, other):
        return self._d.__rtruediv__(self._get_other(other))

    def __floordiv__(self, other):
        return int(self._d.__truediv__(self._get_other(other)))

    def __rfloordiv__(self, other):
        return self._get_other(other).__floordiv__(self._d)
    #
    # def __divmod__(self, other):
    #     return self._d.__divmod__(self._get_other(other))
    #
    # def __rdivmod__(self, other):
    #     return self._d.__divmod__(self._get_other(other))
    #
    def __mod__(self, other):
        return self.__sub__(self._get_other(other).__mul__(self.__floordiv__(self._get_other(other))))

    def __rmod__(self, other):
        return self._get_other(other).__mod__(self._d)

    def __pow__(self, other):
        if self._get_other(other) == 0:
            return 1
        elif int(self._get_other(other) % 2) == 0:
            return self.__pow__(int(self._get_other(other) / 2)) * self.__pow__(int(self._get_other(other) / 2))
        else:
            return self._d * self.__pow__(int(self._get_other(other) / 2)) * self.__pow__(int(self._get_other(other) / 2))

    def __rpow__(self, other):
        return self._get_other(other).__pow__(self._d)

    def __int__(self):
        return self._d.__int__()

    def __float__(self):
        raise self._d

    def __repr__(self):
        return self._d

    def __round__(self, n=None):
        if n is None:
            n = 1

        a, b = self._d.str_ex().split('.')

        return fixed(f'{a}.{b[:n]}')

exports = {
    'decimal': ContractingDecimal,
}