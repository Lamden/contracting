from unittest import TestCase
from seneca.execution.compiler import SenecaCompiler
from seneca.db.orm import Variable, ForeignVariable, Hash, ForeignHash

import astor
from types import ModuleType


class TestSenecaCompiler(TestCase):
    def test_visit_assign_variable(self):
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

    def test_visit_assign_foreign_variable(self):
        code = '''
fv = ForeignVariable(foreign_contract='scoob', foreign_name='kumbucha')
        '''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        env = {'ForeignVariable': ForeignVariable}

        exec(code_str, env)

        fv = env['fv']

        self.assertEqual(fv.key, '__main__.fv')
        self.assertEqual(fv.foreign_key, 'scoob.kumbucha')

    def test_assign_hash_variable(self):
        code = '''
h = Hash()
        '''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        env = {'Hash': Hash}

        exec(code_str, env)

        h = env['h']

        self.assertEqual(h.key, '__main__.h')

    def test_assign_foreign_hash(self):
        code = '''
fv = ForeignHash(foreign_contract='scoob', foreign_name='kumbucha')
        '''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        env = {'ForeignHash': ForeignHash}

        exec(code_str, env)

        fv = env['fv']

        self.assertEqual(fv.key, '__main__.fv')
        self.assertEqual(fv.foreign_key, 'scoob.kumbucha')

    def test_seneca_export_decorator_pops(self):
        code = '''
@seneca_export
def funtimes():
    print('cool')
        '''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertNotIn('@seneca_export', code_str)