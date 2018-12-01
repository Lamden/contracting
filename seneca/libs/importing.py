import types
from seneca.engine.interpreter import Seneca


def import_contract(n):
    code = Seneca.interface.get_code_obj(n)
    m = types.ModuleType(n)

    scope = {
        'rt': {
            'contract': m.__dict__['__name__']
        }
    }
    m.__dict__.update(scope)
    Seneca.interface.execute(code, m.__dict__, is_main=False)

    return m
