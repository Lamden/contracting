from unittest import TestCase
from seneca.execution.compiler import SenecaCompiler
from seneca.db.orm import Variable

import astor
from types import ModuleType

class TestSenecaCompiler(TestCase):
    def test_visit_assign_datatypes(self):
        code = '''
v = Variable()
'''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        env = {'Variable': Variable}

        exec(code_str, env)

        v = env['v']

        self.assertEqual(v.key, '__main__.v')
