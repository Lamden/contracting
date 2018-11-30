import importlib
from seneca.engine.interpreter import Seneca


def import_contract(n):
    return Seneca.interface.get_code_obj(n)
