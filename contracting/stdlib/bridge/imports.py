import importlib
from types import FunctionType, ModuleType
from ...config import PRIVATE_METHOD_PREFIX
from ...db.orm import Datum


class Func:
    def __init__(self, name, args=(), private=False):
        self.name = name

        if private:
            self.name = PRIVATE_METHOD_PREFIX + self.name

        self.args = args

    def is_of(self, f: FunctionType):
        num_args = f.__code__.co_argcount
        if f.__code__.co_name == self.name and f.__code__.co_varnames[:num_args] == self.args:
            return True
        return False


class Var:
    def __init__(self, name, t):
        self.name = PRIVATE_METHOD_PREFIX + name
        self.type = t

    def is_of(self, v):
        if isinstance(v, self.type):
            return True
        return False


def import_module(name):
    return importlib.import_module(name, package=None)


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
