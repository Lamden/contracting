from seneca.engine.interface import SenecaInterface
import types
import functools
from decimal import *

'''

def setUp(self):
    # overwrite_logger_level(0)
    with SenecaInterface(False) as tooling:
        tooling.r.flushall()
        # Store all smart contracts in CONTRACTS_TO_STORE
        import seneca
        test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

        for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                tooling.publish_code_str(contract_name, GENESIS_AUTHOR, code_str, keep_original=True)

        rt = {
            'author': GENESIS_AUTHOR,
            'sender': GENESIS_AUTHOR,
            'contract': 'minter'
        }


def test_store_float(self):
    with SenecaInterface(False) as tooling:
        tooling.execute_function(
            module_path='seneca.contracts.decimal_test.store_float',
            author=GENESIS_AUTHOR,
            sender=GENESIS_AUTHOR,
            stamps=None,
            s='floaty',
            f=Decimal('0.01')
        )

'''

driver = SenecaInterface(concurrent_mode=False,
                         development_mode=True,
                         port=6379,
                         password='')

driver.r.flushdb()
example_code = '''
from seneca.libs.datatypes import hmap

floats = hmap('floats', str, float)

@export
def store_float(s, f):
    floats[s] = f

@export
def read_float(s):
    return floats[s]

@export
def divide_float(s):
    return floats[s] / 2

@export
def add_floats(s1, s2):
    return floats[s1] + floats[s2]
'''

driver.publish_code_str('example_code', 'stuart', example_code, keep_original=True)
c = driver.get_code_obj('example_code')


class SenecaFunction:
    def __init__(self, name, module_path, kwargs):
        self.name = name
        self.module_path = module_path
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return driver.execute_function(
            module_path=self.module_path,
            **kwargs
        )

class ContractWrapper:
    def __init__(self, contract_name, driver):
        contract_code = driver.get_code_obj(contract_name)
        codes = [cd for cd in contract_code.co_consts if type(cd) == types.CodeType]
        for _c in codes:
            name = _c.co_name
            module_path = 'seneca.contracts.{}.{}'.format(contract_name, _c.co_name)
            kwargs = _c.co_varnames
            setattr(self, name, SenecaFunction(name=name, module_path=module_path, kwargs=kwargs))

def get_contract_functions(contract_name, author='stu', sender='stu', stamps=None):
    # returns a tuple of functions that are callable
    contract_code = driver.get_code_obj(contract_name)
    codes = [cd for cd in contract_code.co_consts if type(cd) == types.CodeType]
    funcs = []
    for _c in codes:
        name = _c.co_name
        module_path = 'seneca.contracts.{}.{}'.format(contract_name, _c.co_name)
        kwargs = _c.co_varnames
        funcs.append(SenecaFunction(name=name, module_path=module_path, kwargs=kwargs))
    return funcs


w = ContractWrapper('example_code', driver)
print(dir(w))