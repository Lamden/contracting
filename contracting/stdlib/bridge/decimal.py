from decimal import Decimal

# There is a much better way to do this...


class ContractingDecimal:
    def _get_other(self, other):
        if type(other) == ContractingDecimal:
            return other._d
        elif type(other) == float:
            return Decimal(str(other))
        return other

    def __init__(self, a):
        if type(a) == float:
            a = str(a)

        self._d = Decimal(a)

    def __bool__(self):
        pass

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
        return self._d.__str__()

    def __neg__(self):
        return self._d.__neg__()

    def __pos__(self):
        return self._d.__pos__()

    def __abs__(self):
        return self.__abs__()

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

    def __divmod__(self, other):
        return self._d.__divmod__(self._get_other(other))

    def __rdivmod__(self, other):
        return self._d.__divmod__(self._get_other(other))

    def __mod__(self, other):
        return self._d.__mod__(self._get_other(other))

    def __rmod__(self, other):
        return self._d.__rmod__(self._get_other(other))

    def __floordiv__(self, other):
        return self._d.__floordiv__(self._get_other(other))

    def __rfloordiv__(self, other):
        return self._d.__rfloordiv__(self._get_other(other))

    def __pow__(self, other):
        return self._d.__pow__(self._get_other(other))

    def __rpow__(self, other):
        return self._d.__rpow__(self._get_other(other))

    def __int__(self):
        return self._d.__int__()

    def __float__(self):
        raise Exception('Cannot cast Decimal to float.')

    def __repr__(self):
        return self._d.__repr__()


exports = {
    'decimal': ContractingDecimal,
}