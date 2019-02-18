from seneca.engine.interpret.utils import ReadOnlyException, CompilationException
from os.path import join, dirname
from tests.utils import TestExecutor, captured_output
import redis, unittest, seneca

test_contracts_path = join(dirname(seneca.__path__[0]), 'test_contracts/')
AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'

class TestScope(TestExecutor):

    def tearDown(self):
        self.ex.currency = False
        self.reset()

    def test_scope(self):
        """
            Importing exported functions should pass
        """
        self.ex.execute_code_str("""
from test_contracts.good import one_you_can_export, one_you_can_also_export, one_you_can_also_also_export
one_you_can_export()
one_you_can_also_export()
one_you_can_also_also_export()
        """)

    def test_scope_fail(self):
        """
            Importing protected functions should fail
        """
        with self.assertRaises(ImportError) as context:
            self.ex.execute_code_str("""
from test_contracts.good import one_you_cannot_export
            """)

    def test_globals(self):
        scope = {'rt': {'sender': '123'}}
        with captured_output() as (out, err):
            res = self.ex.execute_code_str("""
from test_contracts.reasonable import reasonable_call
print(reasonable_call())
            """, scope)
            self.assertEqual(out.getvalue().strip(), 'sender: 123, contract: __main__')

    def test_globals_redis(self):
        bk_info = {'sbb_idx': 2, 'contract_idx': 12}
        rt_info = {'rt': {'sender': 'davis', 'author': 'davis'}}
        all_info = {**bk_info, **rt_info}
        with open(join(test_contracts_path, 'sample.sen.py')) as f:
            self.ex.publish_code_str('sample', 'davis', f.read())

        # with captured_output() as (out, err):
        self.ex.execute_code_str("""
from seneca.contracts.sample import do_that_thing
print(do_that_thing())
        """, all_info)
            # self.assertEqual(out.getvalue().strip(), 'sender: davis, author: davis')

    def test_execute_function(self):
        contracts = ['reasonable']
        for contract in contracts:
            with open('{}/{}.sen.py'.format(test_contracts_path, contract)) as f:
                self.ex.publish_code_str(contract, AUTHOR, f.read())

        self.ex.currency = True
        result = self.ex.execute_function('reasonable', 'call_with_args',
                                          AUTHOR, stamps=10000, args=('it is required',), kwargs={
                                            'not_required': 'it is not requried'
                                          })

        self.assertEqual(result['status'], 'success')

    def test_execute_function_invalid(self):
        with self.assertRaises(ImportError) as context:
            result = self.ex.execute_function('seneca.engine.util.make_n_tup',
                                              'also_me', 10000, args=({'x': 'y'},))
            print('Should not print this: ', result)

    def test_execute_function_out_of_gas(self):
        contracts = ['reasonable']
        for contract in contracts:
            with open('{}/{}.sen.py'.format(test_contracts_path, contract)) as f:
                self.ex.publish_code_str(contract, AUTHOR, f.read())

        self.ex.currency = True
        with self.assertRaises(AssertionError) as context:
            result = self.ex.execute_function('reasonable', 'call_with_args',
                                              AUTHOR, 5, args=('it is required',), kwargs={'not_required':'it is not requried'})

if __name__ == '__main__':
    unittest.main()
