from unittest import TestCase
from seneca.execution.compiler import SenecaCompiler
from seneca.db.orm import Variable

class TestSenecaCompiler(TestCase):
    def test_visit_assign_datatypes(self):
        code = '''
v = Variable()

@seneca_export
def funtimes():
    return v
'''
        c = SenecaCompiler(code_str=code, module_name='testing')
        c.compile()
        print(c._exported_methods)
        print(c._mod_code_str)
        a = exec(c._mod_code_str)
        print(a.funtimes())