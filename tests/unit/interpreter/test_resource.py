from seneca.engine.interpreter.utils import ReadOnlyException
from tests.utils import TestExecutor
import unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'


class TestResource(TestExecutor):

    def test_direct_resource(self):
        balances = self.ex.get_resource('currency', 'balances')
        seed_amount = self.ex.get_resource('currency', 'seed_amount')
        self.assertEqual(balances['324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'], seed_amount)

    # NOTE: just don't modify the resources, it's not a security issue because you can ultimately modify the Ledis
    #       data anyways. It will simply not pass on consensus
    def test_direct_resource_modify(self):
        balances = self.ex.get_resource('currency', 'balances')
        with self.assertRaises(AssertionError) as context:
            balances['black_hole'] = 1

    def test_indirect_resource_modify(self):
        balances = self.ex.get_resource('atomic_swap', 'balances')
        with self.assertRaises(AssertionError) as context:
            balances['black_hole'] = 1

    def test_import_modify_resource_of_another_contract(self):
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
from seneca.contracts.currency import balances

@seed
def init():
    balances['222'].value = 11
            """)
        with self.assertRaises(ReadOnlyException) as context:
            self.ex.execute_code_str("""
from seneca.contracts.currency import balances

@seed
def init():
    balances = 11
            """)
        self.ex.execute_code_str("""
from seneca.contracts.currency import balances

@seed
def init():
    balances['stu']
            """)

    def test_import_read_resource_of_another_contract(self):

        self.ex.publish_code_str('xrate_sc', 'man', """
from seneca.contracts.currency import xrate

@export
def use_xrate():
    return xrate + 1
        """)
        res = self.ex.execute_function('xrate_sc', 'use_xrate', 'haha')
        self.assertEqual(res['output'], 2)


if __name__ == '__main__':
    unittest.main()
