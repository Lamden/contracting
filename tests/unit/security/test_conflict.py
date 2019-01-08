from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca, os

os.environ['CIRCLECI'] = 'true'

test_contracts_path = seneca.__path__[0] + '/test_contracts/'

c_1 = """
from seneca.libs.datatypes import hmap
resource = hmap('resource', str, int)

@seed
def seed():
    resource['stu'] = 1337
    resource['davis'] = 999

@export
def read_resource(string):
    return resource[string]

@export
def write_resource(string, value):
    resource[string] = value
"""

c_2 = """
from seneca.contracts.c_1 import read_resource as r
from seneca.contracts.c_1 import write_resource as w

from seneca.libs.datatypes import hmap
resource = hmap('resource', str, int)

@seed
def seed():
    resource['stu'] = 888
    resource['davis'] = 7777

@export
def read_resource(string):
    return resource[string]

@export
def read_other_resource(string):
    return r(string)

@export
def corrupt_resource(string, value):
    w(string=string, value=value)

"""

class TestConflict(TestInterface):

    def test_publish_code_str(self):
        """
            Testing to see if the submission to Redis works.
        """
        self.si.publish_code_str('c_1', 'anonymoose', c_1)
        self.si.publish_code_str('c_2', 'anonymoose', c_2)
        self.si.execute_code_str("""
from seneca.contracts.c_1 import read_resource as rr1
from seneca.contracts.c_2 import read_resource as rr2, read_other_resource as ror2, corrupt_resource as cr2

cr2(string='stu', value=100)
cr2(string='davis', value=123)

print(rr1(string='stu'))
print(rr1(string='davis'))
print(rr2(string='stu'))
print(rr2(string='davis'))
        """)




if __name__ == '__main__':
    unittest.main()
