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
        c = SenecaCompiler(code_str=code, module_name='testing')
        c.compile()
        c._ast_tree = ast.fix_missing_locations(c._ast_tree)
        print(astor.to_source(c._ast_tree))