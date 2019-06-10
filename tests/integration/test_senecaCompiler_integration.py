from unittest import TestCase
from contracting.compilation.compiler import ContractingCompiler
from contracting.stdlib import env
import re
import astor
from contracting import config


class TestSenecaCompiler(TestCase):
    def test_visit_assign_variable(self):
        code = '''
v = Variable()
'''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        v = scope['__v']

        self.assertEqual(v._key, '__main__.v')

    def test_visit_assign_foreign_variable(self):
        code = '''
fv = ForeignVariable(foreign_contract='scoob', foreign_name='kumbucha')
        '''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['__fv']

        self.assertEqual(fv._key, '__main__.fv')
        self.assertEqual(fv.foreign_key, 'scoob.kumbucha')

    def test_assign_hash_variable(self):
        code = '''
h = Hash()
        '''
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        h = scope['__h']

        self.assertEqual(h._key, '__main__.h')

    def test_assign_foreign_hash(self):
        code = '''
fv = ForeignHash(foreign_contract='scoob', foreign_name='kumbucha')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        scope = env.gather()

        exec(code_str, scope)

        fv = scope['__fv']

        self.assertEqual(fv._key, '__main__.fv')
        self.assertEqual(fv.foreign_key, 'scoob.kumbucha')

    def test_export_decorator_pops(self):
        code = '''
@export
def funtimes():
    print('cool')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertNotIn('@export', code_str)

    def test_private_function_prefixes_properly(self):
        code = '''
def private():
    print('cool')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertIn('__private', code_str)

    def test_private_func_call_in_public_func_properly_renamed(self):
        code = '''
@export
def public():
    private('hello')
    
def private(message):
    print(message)
'''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

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
        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

        self.assertEqual(len([m.start() for m in re.finditer(config.PRIVATE_METHOD_PREFIX, code_str)]), 9)


    def test_construct_renames_properly(self):
        code = '''
@construct
def seed():
    print('yes')

@export
def hello():
    print('no')
    
def goodbye():
    print('idk')
        '''

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

    def test_token_contract_parses_correctly(self):

        f = open('./test_contracts/currency.s.py')
        code = f.read()
        f.close()

        c = ContractingCompiler()
        comp = c.parse(code, lint=False)
        code_str = astor.to_source(comp)

    def test_oot(self):
        code = '''
supply = Variable()
balances = Hash(default_value=0)

@construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100
    supply.set(balances['stu'] + balances['colin'])

@export
def transfer(amount, to):
    sender = ctx.caller
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount

@export
def balance_of(account):
    return balances[account]

@export
def total_supply():
    return supply.get()

@export
def allowance(owner, spender):
    return balances[owner, spender]

@export
def approve(amount, to):
    sender = ctx.caller
    balances[sender, to] += amount
    return balances[sender, to]

@export
def transfer_from(amount, to, main_account):
    sender = ctx.caller

    assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, sender], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount

'''
        c = ContractingCompiler()
        comp = c.parse(code, lint=True)
        code_str = astor.to_source(comp)
        print(code_str)
