from tests.utils import captured_output, TestExecutor
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

class TestCallScope(TestExecutor):

    def test_call_scope(self):
        self.flush()
        self.ex.publish_code_str('c_2', AUTHOR, c_2)
        self.ex.publish_code_str('c_1', AUTHOR, c_1)
        self.ex.execute_code_str("""
from seneca.contracts.c_1 import call_me
call_me()
        """)
        self.assertEqual(self.ex.r.get('c_1:my_number:__main__'), b'"1234567890"')
        self.assertEqual(self.ex.r.get('c_2:my_number:c_1'), b'"1234"')

    def test_call_scope_execute_function(self):
        self.flush()
        self.ex.publish_code_str('c_2', AUTHOR, c_2)
        self.ex.publish_code_str('c_1', AUTHOR, c_1)
        self.ex.execute_function('c_1', 'call_me', AUTHOR, 10000)
        self.assertEqual(self.ex.r.get('c_1:my_number:{}'.format(AUTHOR)), b'"1234567890"')
        self.assertEqual(self.ex.r.get('c_2:my_number:c_1'), b'"1234"')

if __name__ == '__main__':
    unittest.main()
