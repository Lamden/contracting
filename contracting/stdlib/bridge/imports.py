import importlib
from types import FunctionType, ModuleType
from ...config import PRIVATE_METHOD_PREFIX
from ...db.orm import Datum


class Func:
    def __init__(self, name, args, private=False):
        self.name = name

        if private:
            self.name = PRIVATE_METHOD_PREFIX + self.name

        self.args = args

    def is_of(self, f: FunctionType):
        if f.__code__.co_name == self.name and f.__code__.co_varnames == self.args:
            return True
        return False


class Var:
    def __init__(self, name, t):
        self.name = name
        self.type = t

    def is_of(self, v):
        if isinstance(v, self.type) and v.name == self.name:
            return True
        return False


def import_module(name):
    importlib.import_module(name)


def enforce_interface(m: ModuleType, interface: list):
    implemented = vars(m)

    for i in interface:
        attribute = implemented.get(i.name)
        if attribute is None:
            return False

        # Branch for data types
        if isinstance(attribute, Datum):
            if not i.is_of(attribute):
                return False

        if isinstance(attribute, FunctionType):
            if not i.is_of(attribute):
                return False
    return True
