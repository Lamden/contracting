from seneca.engine.interpret.utils import ReadOnlyException, CompilationException
from seneca.engine.interpret.parser import Parser
from tests.utils import TestExecutor
import redis, unittest, seneca, os
from decimal import *

os.environ['CIRCLECI'] = 'true'

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

c_3 = """
from seneca.libs.storage.datatypes import Map, Resource
resource = Map('resource')
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

from seneca.libs.storage.datatypes import Map, Resource
resource = Map('resource')
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

"""

class TestConflict(TestExecutor):

    def test_conflict(self):
        """
            Testing to see if the submission to Redis works.
        """
        self.flush()
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        self.ex.execute_code_str("""
from seneca.contracts.c_3 import read_resource as rr1
from seneca.contracts.c_4 import read_resource as rr2, read_other_resource as ror2, corrupt_resource as cr2

cr2(string='stu', value=100)
cr2(string='davis', value=123)

res1 = rr1(string='stu')
res2 = rr1(string='davis')
res3 = rr2(string='stu')
res4 = rr2(string='davis')

        """)
        self.assertEqual(Parser.parser_scope['res1'], Decimal(100))
        self.assertEqual(Parser.parser_scope['res2'], Decimal(123))
        self.assertEqual(Parser.parser_scope['res3'], Decimal(888))
        self.assertEqual(Parser.parser_scope['res4'], Decimal(7777))

    def test_repeated_variables_inside_different_contracts_set(self):
        self.flush()
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        self.assertEqual(self.ex.r.hget('c_3', 'shared_name'), '{}@Decimal'.format(3).encode())
        self.assertEqual(self.ex.r.hget('c_4', 'shared_name'), '{}@Decimal'.format(5).encode())


    def test_repeated_variables_inside_different_contracts_get(self):
        self.flush()
        self.ex.publish_code_str('c_3', 'anonymoose', c_3)
        self.ex.publish_code_str('c_4', 'anonymoose', c_4)
        res = self.ex.execute_function('c_3', 'read_shared_name', 'anonymoose')
        self.assertEqual(res['output'], 10)
        self.assertEqual(type(res['output']), Decimal)


if __name__ == '__main__':
    unittest.main()
