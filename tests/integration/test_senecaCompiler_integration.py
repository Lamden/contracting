from unittest import TestCase
from seneca.execution.compiler import SenecaCompiler
from seneca.db.orm import Variable

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
        c = SenecaCompiler()
        comp = c.parse(code)
        print(astor.to_source(comp))
