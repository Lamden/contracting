from decimal import Decimal


class ContractingDecimal:
    def __init__(self, a):
        if type(a) == float:
            a = str(a)

        self._d = Decimal(a)

    def __add__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__add__(self, other)

    def __sub__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__sub__(self, other)

    def __mul__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__mul__(self, other)

    def __truediv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__truediv__(self, other)

    def __divmod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__divmod__(self, other)

    def __mod__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__mod__(self, other)

    def __floordiv__(self, other):
        if type(other) == float:
            other = Decimal(str(other))
        return self._d.__floordiv__(self, other)

    def __float__(self):
        raise Exception('Cannot cast Decimal to float.')


exports = {
    'decimal': ContractingDecimal,
}