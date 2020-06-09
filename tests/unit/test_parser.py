from contracting.compilation import parser
from contracting.compilation.compiler import ContractingCompiler
from unittest import TestCase


class TestParser(TestCase):
    def setUp(self):
        self.compiler = ContractingCompiler()

    def test_methods_for_contract_single_function(self):
        code = '''
@export
def test_func(arg: str, arg2: int):
    return arg, arg2
        '''

        compiled = self.compiler.parse_to_code(code)

        expected = [{
            'name': 'test_func',
            'arguments': [
                {
                    'name': 'arg',
                    'type': 'str'
                },
                {
                    'name': 'arg2',
                    'type': 'int'
                }
            ]
        }]

        got = parser.methods_for_contract(compiled)

        self.assertListEqual(expected, got)

    def test_methods_for_contract_multiple_functions_and_privates(self):
        code = '''
@export
def test_func(arg: str, arg2: int):
    return arg, arg2
    
@export
def another_one(something: Any, something_else: dict):
    a = 123
    b = 456
    return add(a, b)
    
def add(a, b):
    return a + b
'''
        compiled = self.compiler.parse_to_code(code)

        expected = [{
            'name': 'test_func',
            'arguments': [
                {
                    'name': 'arg',
                    'type': 'str'
                },
                {
                    'name': 'arg2',
                    'type': 'int'
                }
            ],
        },
        {
            'name': 'another_one',
            'arguments': [
                {
                    'name': 'something',
                    'type': 'Any'
                },
                {
                    'name': 'something_else',
                    'type': 'dict'
                }
            ]
        }]

        got = parser.methods_for_contract(compiled)

        self.assertListEqual(expected, got)

    def test_variables_for_contract_passes_election_house(self):
        code = '''
# Convenience
I = importlib

#Policies
policies = Hash()

# Policy interface
policy_interface = [
    I.Func('vote', args=('vk', 'obj')),
    I.Func('current_value')
]

@export
def register_policy(contract: str):
    if policies[contract] is None:
        # Attempt to import the contract to make sure it is already submitted
        p = I.import_module(contract)

        # Assert ownership is election_house and interface is correct
        assert I.owner_of(p) == ctx.this, \
            'Election house must control the policy contract!'

        assert I.enforce_interface(p, policy_interface), \
            'Policy contract does not follow the correct interface'

        policies[contract] = True
    else:
        raise Exception('Policy already registered')

@export
def current_value_for_policy(policy: str):
    assert policies.get(policy) is not None, 'Invalid policy.'
    p = I.import_module(policy)

    return p.current_value()

@export
def vote(policy: str, value: Any):
    # Verify policy has been registered
    assert policies.get(policy) is not None, 'Invalid policy.'
    p = I.import_module(policy)

    p.vote(vk=ctx.caller, obj=value)
    '''

        compiled = self.compiler.parse_to_code(code)

        got = parser.variables_for_contract(compiled)

        expected = {
            'variables': [],
            'hashes': ['policies']
        }

        self.assertDictEqual(got, expected)

    def test_variables_for_contract_multiple_variables(self):
        code = '''
v1 = Variable()
v2 = Variable()
v3 = Variable()

@export
def something():
   return 1
        '''

        compiled = self.compiler.parse_to_code(code)

        got = parser.variables_for_contract(compiled)

        expected = {
            'variables': ['v1', 'v2', 'v3'],
            'hashes': []
        }

        self.assertDictEqual(got, expected)

    def test_variables_for_contract_multiple_hashes(self):
        code = '''
h1 = Hash()
h2 = Hash()
h3 = Hash()

@export
def something():
   return 1
        '''

        compiled = self.compiler.parse_to_code(code)

        got = parser.variables_for_contract(compiled)

        expected = {
            'variables': [],
            'hashes': ['h1', 'h2', 'h3']
        }

        self.assertDictEqual(got, expected)

    def test_variables_mix(self):
        code = '''
v1 = Variable()
v2 = Variable()
v3 = Variable()
h1 = Hash()
h2 = Hash()
h3 = Hash()

@export
def something():
   return 1
        '''

        compiled = self.compiler.parse_to_code(code)

        got = parser.variables_for_contract(compiled)

        expected = {
            'variables': ['v1', 'v2', 'v3'],
            'hashes': ['h1', 'h2', 'h3']
        }

        self.assertDictEqual(got, expected)
