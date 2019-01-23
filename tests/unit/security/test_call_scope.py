from unittest import TestCase
from seneca.engine.interface import SenecaInterface, Seneca
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca, os
from decimal import *

os.environ['CIRCLECI'] = 'true'

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

c_1 = """
from seneca.libs.datatypes import hmap
from seneca.contracts.c_2 import call_me_maybe

my_number = hmap('my_number', str, str)

@export
def call_me():
    my_number[rt['sender']] = '1234567890'
    call_me_maybe()
"""

c_2 = """
from seneca.libs.datatypes import hmap

my_number = hmap('my_number', str, str)

@export
def call_me_maybe():
    my_number[rt['sender']] = '0987654321'
    call_here()

@export
def call_here():
    my_number[rt['sender']] = '1234'

"""

AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'

class TestCallScope(TestInterface):

    def setUp(self):
        super().setUp()
        CONTRACTS_TO_STORE = {
            'currency': 'currency.sen.py'
        }
        test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

        for contract_name, file_name in CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                self.si.publish_code_str(contract_name, AUTHOR, code_str)

    def test_call_scope(self):
        self.si.publish_code_str('c_2', AUTHOR, c_2)
        self.si.publish_code_str('c_1', AUTHOR, c_1)
        self.si.execute_code_str("""
from seneca.contracts.c_1 import call_me
call_me()
        """)
        self.assertTrue(self.si.r.exists('c_1:my_number:anonymous'))
        self.assertTrue(self.si.r.exists('c_2:my_number:c_1'))
        self.assertEqual(self.si.r.get('c_2:my_number:c_1'), b'"1234"')

    def test_call_scope_execute_function(self):
        self.si.publish_code_str('c_2', AUTHOR, c_2)
        self.si.publish_code_str('c_1', AUTHOR, c_1)
        self.si.bypass_currency = True
        self.si.execute_function('seneca.contracts.currency.mint', AUTHOR, 0, to=AUTHOR, amount=10000)
        self.si.bypass_currency = False
        self.si.execute_function('seneca.contracts.c_1.call_me', AUTHOR, 10000)
        self.assertTrue(self.si.r.exists('c_1:my_number:{}'.format(AUTHOR)))
        self.assertTrue(self.si.r.exists('c_2:my_number:c_1'))
        self.assertEqual(self.si.r.get('c_2:my_number:c_1'), b'"1234"')

if __name__ == '__main__':
    unittest.main()
