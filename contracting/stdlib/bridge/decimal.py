from decimal import Decimal

# There is a much better way to do this...

class ContractingDecimal:
    def __init__(self, a):
        if type(a) == float:
            a = str(a)

        self._d = Decimal(a)

    def __bool__(self):
        pass

    def __eq__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__eq__(other)

    def __lt__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__lt__(other)

    def __le__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__le__(other)

    def __gt__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__gt__(other)

    def __ge__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__ge__(other)

    def __str__(self):
        return self._d.__str__()

    def __neg__(self):
        return self._d.__neg__()

    def __pos__(self):
        return self._d.__pos__()

    def __abs__(self):
        return self.__abs__()

    def __add__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__add__(other)

    def __radd__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__radd__(other)

    def __sub__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__sub__(other)

    def __rsub__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rsub__(other)

    def __mul__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__mul__(other)

    def __rmul__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rmul__(other)

    def __truediv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__truediv__(other)

    def __rtruediv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rtruediv__(other)

    def __divmod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__divmod__(other)

    def __rdivmod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__divmod__(other)

    def __mod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__mod__(other)

    def __rmod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rmod__(other)

    def __floordiv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__floordiv__(other)

    def __rfloordiv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rfloordiv__(other)

    def __pow__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__pow__(other)

    def __rpow__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__rpow__(other)

    def __int__(self):
        return self._d.__int__()

    def __float__(self):
        raise Exception('Cannot cast Decimal to float.')


exports = {
    'decimal': ContractingDecimal,
}