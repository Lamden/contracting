from seneca.engine.interpreter.parser import Parser
from tests.utils import TestExecutor
from seneca.libs.storage.datatypes import Hash
import ledis, unittest, seneca, os
from decimal import *

os.environ['CIRCLECI'] = 'true'

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

restaurant_a = """
from seneca.libs.storage.datatypes import Hash
my_breads = Hash('my_breads')

@seed
def initialize():
    my_breads['rye'] = 15.4

@export
def this_bread(bread):
    return my_breads[bread]
    
@export
def change_bread(bread, amount):
    my_breads[bread] = amount

"""

restaurant_b = """
from seneca.libs.storage.datatypes import Hash
my_breads = Hash('my_breads')

@seed
def initialize():
    my_breads['rye'] = 22.2

@export
def this_bread(bread):
    return my_breads[bread]
    
@export
def change_bread(bread, amount):
    my_breads[bread] = amount

"""

restaurant_c = """
from seneca.contracts.restaurant_b import my_breads as b_breads
c_breads = Hash('my_breads')

@seed
def initialize():
    c_breads['rye'] = 11.7
    
def this_bread(bread):
    return b_breads[bread] + c_breads[bread]
    
@export
def change_bread(bread, amount):
    c_breads[bread] = amount

"""


class TestKeyCollision(TestExecutor):

    def setUp(self):
        super().setUp()
        self.flush()

    def test_same_variable_function_names(self):
        self.ex.publish_code_str('restaurant_a', 'anonymoose', restaurant_a)
        self.ex.publish_code_str('restaurant_b', 'anonymoose', restaurant_b)
        res = self.ex.execute_function('restaurant_a', 'this_bread', 'anonymoose', kwargs={'bread': 'rye'})
        self.assertEqual(res['output'], Decimal('15.4'))
        res = self.ex.execute_function('restaurant_b', 'this_bread', 'anonymoose', kwargs={'bread': 'rye'})
        self.assertEqual(res['output'], Decimal('22.2'))
        self.ex.execute_function('restaurant_a', 'change_bread', 'anonymoose', kwargs={'bread': 'rye', 'amount': 4.45})
        res = self.ex.execute_function('restaurant_a', 'this_bread', 'anonymoose', kwargs={'bread': 'rye'})
        self.assertEqual(res['output'], Decimal('4.45'))

    def test_same_variable_function_names_with_imported(self):
        self.ex.publish_code_str('restaurant_a', 'anonymoose', restaurant_a)
        self.ex.publish_code_str('restaurant_b', 'anonymoose', restaurant_b)
        self.ex.publish_code_str('restaurant_c', 'anonymoose', restaurant_c)
        res = self.ex.execute_function('restaurant_c', 'this_bread', 'anonymoose', kwargs={'bread': 'rye'})
        self.assertEqual(res['output'], Decimal('33.9'))


if __name__ == '__main__':
    unittest.main()
