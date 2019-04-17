from unittest import TestCase
from seneca.execution.compiler import SenecaCompiler
from seneca.db.orm import Variable

import ast
import astor
class TestSenecaCompiler(TestCase):
    def test_visit_assign_datatypes(self):
        code = '''
v = Variable()

@seneca_export
def funtimes():
    return v
    
def private():
    print('yeehaw')
'''
        c = SenecaCompiler(module_name='testing')
        comp = c.compile(code)
        print(comp)
