from unittest import TestCase
from seneca.ast.compiler import SenecaCompiler
from seneca.stdlib import env
import re
import astor
from seneca import config


class TestSenecaCompiler(TestCase):
    def test_visit_assign_variable(self):
        code = '''
v = Variable()
'''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        v = scope['v']

        self.assertEqual(v.key, '__main__.v')

    def test_visit_assign_foreign_variable(self):
        code = '''
fv = ForeignVariable(foreign_contract='scoob', foreign_name='kumbucha')
        '''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['fv']

        self.assertEqual(fv.key, '__main__.fv')
        self.assertEqual(fv.foreign_key, 'scoob.kumbucha')

    def test_assign_hash_variable(self):
        code = '''
h = Hash()
        '''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        h = scope['h']

        self.assertEqual(h.key, '__main__.h')

    def test_assign_foreign_hash(self):
        code = '''
fv = ForeignHash(foreign_contract='scoob', foreign_name='kumbucha')
        '''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['fv']

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

    def test_private_function_prefixes_properly(self):
        code = '''
def private():
    print('cool')
        '''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertIn('__private', code_str)

    def test_private_func_call_in_public_func_properly_renamed(self):
        code = '''
@seneca_export
def public():
    private('hello')
    
def private(message):
    print(message)
'''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        print(code_str)

        # there should be two private occurances of the method call
        self.assertEqual(len([m.start() for m in re.finditer('__private', code_str)]), 2)

    def test_private_func_call_in_other_private_functions(self):
        code = '''
def a():
    b()
    
def b():
    c()
    
def c():
    e()
    
def d():
    print('hello')
    
def e():
    d()        
'''
        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertEqual(len([m.start() for m in re.finditer(config.PRIVATE_METHOD_PREFIX, code_str)]), 9)

    def test_seneca_construct_renames_properly(self):
        code = '''
@seneca_construct
def seed():
    print('yes')

@seneca_export
def hello():
    print('no')
    
def goodbye():
    print('idk')
        '''

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)
        print(code_str)

    def test_token_contract_parses_correctly(self):

        f = open('./test_contracts/currency.s.py')
        code = f.read()
        f.close()

        c = SenecaCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        print(code_str)
