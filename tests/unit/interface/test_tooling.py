from unittest import TestCase
from seneca.tooling import *
from decimal import *

example_code = '''
from seneca.libs.datatypes import hmap

floats = hmap('floats', str, float)

@export
def store_float(s, f):
    floats[s] = f

@export
def read_float(s):
    return floats[s]

@export
def divide_float(s):
    return floats[s] / 2

@export
def add_floats(s1, s2):
    return floats[s1] + floats[s2]
'''


class TestSenecaTooling(TestCase):
    def setUp(self):
        self.driver = SenecaInterface(concurrent_mode=False,
                           port=6379,
                           password='')
        self.driver.r.flushdb()

    def test_submission(self):
        self.driver.publish_code_str(
            'example_code',
            author='stuart',
            code_str=example_code,
        )

        self.assertEqual(example_code, self.driver.get_contract_meta('example_code')['code_str'])

    def test_wrapper(self):
        self.driver.publish_code_str(
            'example_code',
            author='stuart',
            code_str=example_code,
        )

        wrapper = ContractWrapper('example_code', driver=self.driver, default_sender='stuart')
        expected_functions = {'store_float', 'read_float', 'divide_float', 'add_floats'}

        self.assertEqual(expected_functions - set(dir(wrapper)), set())

    def test_call_function(self):
        self.driver.publish_code_str(
            'example_code',
            author='stuart',
            code_str=example_code,
        )

        wrapper = ContractWrapper('example_code', driver=self.driver, default_sender='stuart')
        wrapper.store_float(s='stu', f=0.1234)
        f = wrapper.read_float(s='stu')

        self.assertEqual(f['output'], Decimal('0.1234'))

if __name__ == '__main__':
    import unittest
    unittest.main()
