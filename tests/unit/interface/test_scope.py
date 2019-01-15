from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException, CompilationException
from os.path import join
from tests.utils import captured_output, TestInterface
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/../test_contracts/'
AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'

class TestScope(TestInterface):

    def setUp(self):
        with SenecaInterface(False) as interface:
            interface.r.flushall()
        super().setUp()

    def test_scope(self):
        """
            Importing exported functions should pass
        """
        self.si.execute_code_str("""
from test_contracts.good import one_you_can_export, one_you_can_also_export, one_you_can_also_also_export
one_you_can_export()
one_you_can_also_export()
one_you_can_also_also_export()
        """)

    def test_scope_fail(self):
        """
            Importing protected functions should fail
        """
        with self.assertRaises(CompilationException) as context:
            self.si.execute_code_str("""
from test_contracts.good import one_you_cannot_export
            """)

    def test_globals(self):
        scope = {'rt': {'sender':'123'}}
        res = self.si.execute_code_str("""
from test_contracts.reasonable import reasonable_call
result = reasonable_call()
        """, scope)
        self.assertEqual(res, 'sender: 123, contract: test_contracts.reasonable')

    def test_globals_redis(self):
        bk_info = {'sbb_idx': 2, 'contract_idx': 12}
        rt_info = {'rt': {'sender': 'davis', 'author': 'davis'}}
        all_info = {**bk_info, **rt_info}
        with open(join(test_contracts_path, 'sample.sen.py')) as f:
            self.si.publish_code_str('sample', 'davis', f.read())
            res = self.si.execute_code_str("""
from seneca.contracts.sample import do_that_thing
result = do_that_thing()
            """, all_info)
            self.assertEqual(res, 'sender: davis, author: davis')

    def test_execute_function(self):
        contracts = ['currency', 'reasonable']
        for contract in contracts:
            with open('{}/{}.sen.py'.format(test_contracts_path, contract)) as f:
                self.si.publish_code_str(contract, AUTHOR, f.read())

        result = self.si.execute_function('seneca.contracts.reasonable.call_with_args',
                                          AUTHOR, 10000, 'it is required', not_required='it is not requried')

        self.assertEqual(result['status'], 'success')

    def test_execute_function_invalid(self):
        with open('{}/currency.sen.py'.format(test_contracts_path)) as f:
            self.si.publish_code_str('currency', AUTHOR, f.read())
        with self.assertRaises(ImportError) as context:
            result = self.si.execute_function('seneca.engine.util.make_n_tup',
                                              'also_me', 10000, {'x': 'y'})
            print('Should not print this: ', result)

    def test_execute_function_out_of_gas(self):
        contracts = ['currency', 'reasonable']
        for contract in contracts:
            with open('{}/{}.sen.py'.format(test_contracts_path, contract)) as f:
                self.si.publish_code_str(contract, AUTHOR, f.read())
                
        with self.assertRaises(AssertionError) as context:
            result = self.si.execute_function('seneca.contracts.reasonable.call_with_args',
                                              AUTHOR, 5, 'it is required', not_required='it is not requried')

if __name__ == '__main__':
    unittest.main()
