from seneca.engine.interpreter.parser import Parser
from tests.utils import TestExecutor
from seneca.libs.storage.datatypes import Hash
import ledis, unittest, seneca, os
from decimal import *

os.environ['CIRCLECI'] = 'true'

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

c_3 = """
from seneca.libs.storage.datatypes import Hash, Resource
resource = Hash('resource')
shared_name = Resource()
sandles = Resource()

@seed
def initialize():
    resource['stu'] = 1337
    resource['davis'] = 999
    shared_name = 3

@export
def read_resource(string):
    return resource[string]

@export
def write_resource(string, value):
    resource[string] = value
    
@export
def read_shared_name():
    t = 7 + shared_name
    return t
    
"""

c_4 = """
from seneca.contracts.c_3 import read_resource as r
from seneca.contracts.c_3 import write_resource as w

from seneca.libs.storage.datatypes import Hash, Resource
resource = Hash('resource')
shared_name = Resource()
shoes = Resource()

@seed
def initialize():
    resource['stu'] = 888
    resource['davis'] = 7777
    shared_name = 5

@export
def read_resource(string):
    return resource[string]

@export
def read_other_resource(string):
    return r(string)

@export
def corrupt_resource(string, value):
    w(string=string, value=value)
    
@export
def read_shared_name():
    t = 7 + shared_name
    return t
    
@export
def read_shared_name_aug_assign():
    shared_name += 3
    return shared_name

"""


class TestConflict(TestExecutor):

    def setUp(self):
        super().setUp()
        self.flush()

    def test_upload_modify_upload(self):
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        res = self.ex.execute_function('c_3', 'write_resource', 'anonymoose', kwargs={'string': 'stu', 'value': 23})
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        res = self.ex.execute_function('c_3', 'read_resource', 'anonymoose', kwargs={'string': 'stu'})
        self.assertEqual(res['output'], 23)

    def test_conflict(self):
        """
            Testing to see if the submission to Ledis works.
        """
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        self.ex.execute_code_str("""
from seneca.contracts.c_3 import read_resource as rr1
from seneca.contracts.c_4 import read_resource as rr2, read_other_resource as ror2, corrupt_resource as cr2

@seed
def init():
    cr2(string='stu', value=100)
    cr2(string='davis', value=123)
    
    res1 = rr1(string='stu')
    res2 = rr1(string='davis')
    res3 = rr2(string='stu')
    res4 = rr2(string='davis')

        """)
        self.assertEqual(self.ex.driver.hget('Hash:c_3:resource', 'stu'), b'100')
        self.assertEqual(self.ex.driver.hget('Hash:c_3:resource', 'davis'), b'123')
        self.assertEqual(self.ex.driver.hget('Hash:c_4:resource', 'stu'), b'888')
        self.assertEqual(self.ex.driver.hget('Hash:c_4:resource', 'davis'), b'7777')

    def test_repeated_variables_inside_different_contracts_set(self):
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        self.assertEqual(self.ex.driver.hget('Resource:c_3', 'shared_name'), b'3')
        self.assertEqual(self.ex.driver.hget('Resource:c_4', 'shared_name'), b'5')

    def test_repeated_variables_inside_different_contracts_get(self):
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        res = self.ex.execute_function('c_3', 'read_shared_name', 'anonymoose')
        self.assertEqual(res['output'], 10)
        self.assertEqual(type(res['output']), Decimal)

    def test_repeated_variables_inside_different_contracts_aug_set_get(self):
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        res = self.ex.execute_function('c_4', 'read_shared_name_aug_assign', 'anonymoose')
        self.assertEqual(res['output'], 8)
        self.assertEqual(type(res['output']), Decimal)
        res = self.ex.execute_function('c_4', 'read_shared_name_aug_assign', 'anonymoose')
        self.assertEqual(res['output'], 11)
        self.assertEqual(type(res['output']), Decimal)

    def test_map_collide(self):
        with self.assertRaises(AssertionError) as context:
            balances = Hash('balances')
            balances['hey'] = Hash('palanaces')
            balances['hey']['ok'] = 1
            malances = Hash('balances')

    def test_mixed_scope(self):
        # NOTE: Should pass
        self.ex.publish_code_str('msmsmsms_contract', 'AUTHOR', """
@export
def msmsmsms():
    pass
        """)
        self.ex.execute_code_str("""
@seed
def init():
    msmsmsms = 1
        """)

if __name__ == '__main__':
    unittest.main()
