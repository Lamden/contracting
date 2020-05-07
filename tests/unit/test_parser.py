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