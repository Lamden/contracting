from tests.utils import TestExecutor
import unittest, seneca, os
from seneca.engine.book_keeper import BookKeeper
from seneca.engine.conflict_resolution import CRContext
from decimal import *

os.environ['CIRCLECI'] = 'true'

test_contracts_path = os.path.dirname(seneca.__path__[0]) + '/test_contracts/'

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

STU = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
DAVIS = 'a103715914a7aae8dd8fddba945ab63a169dfe6e37f79b4a58bcf85bfd681694'


class TestKeyCollision(TestExecutor):

    def setUp(self):
        super().setUp()
        self.flush()

    def _build_info_dict(self, sbb_idx=0, contract_idx=0, master_db='', working_db=''):
        master_db = master_db or 'some placeholder that irl would be a ledis client cursor'
        working_db = working_db or 'another placeholder that irl would be a ledis client cursor'
        data = CRContext(working_db=working_db, master_db=master_db, sbb_idx=sbb_idx)

        info = {'sbb_idx': sbb_idx, 'contract_idx': contract_idx, 'data': data}
        return info

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

    def test_stubucks_collision(self):
        with open('{}/new_stubucks.sen.py'.format(test_contracts_path)) as f:
            self.ex.publish_code_str('stubucks', 'anonymoose', f.read())
        res = self.ex.execute_function('stubucks', 'transfer', STU, kwargs={
            'to': DAVIS,
            'amount': 1337
        })
        balances = self.ex.get_resource('stubucks', 'balances')
        self.assertEqual(balances[STU], Decimal('998663'))
        self.assertEqual(balances[DAVIS], Decimal('1337'))

    # def test_stubucks_collision_with_cr(self):
    #     with open('{}/new_stubucks.sen.py'.format(test_contracts_path)) as f:
    #         self.ex.publish_code_str('stubucks', 'anonymoose', f.read())
    #     self.ex.concurrency = True
    #     expected_info = self._build_info_dict(sbb_idx=0, contract_idx=1)
    #     BookKeeper.set_cr_info(**expected_info)
    #     res = self.ex.execute_function('stubucks', 'transfer', STU, kwargs={
    #         'to': DAVIS,
    #         'amount': 1337
    #     })
    #     print(res)
    #     balances = self.ex.get_resource('stubucks', 'balances')
    #     self.assertEqual(balances[STU], Decimal('998663'))
    #     self.assertEqual(balances[DAVIS], Decimal('1337'))


if __name__ == '__main__':
    unittest.main()
