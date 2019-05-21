from ...db.orm import Variable, Hash, ForeignVariable, ForeignHash
from ...db.contract import Contract
from ...execution.runtime import rt


class V(Variable):
    def __init__(self, *args, **kwargs):
        if rt.env.get('__Driver') is not None:
            super().__init__(self, driver=rt.env.get('__Driver'), *args, **kwargs)
        else:
            super().__init__(self, *args, **kwargs)


class HV(Hash):
    def __init__(self, *args, **kwargs):
        if rt.env.get('__Driver') is not None:
            super().__init__(self, driver=rt.env.get('__Driver'), *args, **kwargs)
        else:
            super().__init__(self, *args, **kwargs)


class FV(ForeignVariable):
    def __init__(self, *args, **kwargs):
        if rt.env.get('__Driver') is not None:
            super().__init__(self, driver=rt.env.get('__Driver'), *args, **kwargs)
        else:
            super().__init__(self, *args, **kwargs)


class FH(ForeignHash):
    def __init__(self, *args, **kwargs):
        if rt.env.get('__Driver') is not None:
            super().__init__(self, driver=rt.env.get('__Driver'), *args, **kwargs)
        else:
            super().__init__(self, *args, **kwargs)


# Define the locals that will be available for smart contracts at runtime
exports = {
    'Variable': Variable,
    'Hash': Hash,
    'ForeignVariable': ForeignVariable,
    'ForeignHash': ForeignHash,
    '__Contract': Contract
}