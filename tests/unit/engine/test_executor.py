import unittest
from seneca.execution.executor import Sandbox, Executor, MultiProcessingSandbox
import sys
import glob
# Import ContractDriver and AbstractDatabaseDriver for property type
# assertions for self.e.driver
from seneca.db.driver import AbstractDatabaseDriver, ContractDriver
from seneca.interpreter.module import DatabaseFinder


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.e = Executor()

    def tearDown(self):
        del self.e

    def test_init(self):
        self.assertEqual(self.e.metering, True, 'Metering not set to true by default.')

    def test_dynamic_init(self):
        e = Executor(metering=False)

        self.assertEqual(e.metering, False, 'Metering is not set to false after dynamic set')

    def test_driver_resolution(self):
        # The CRDriver class is not able to be isolated so this test is turned off for now
        # Colin TODO: Discuss with Davis how we update CRDriver (or isolate the concept)
        #self.assertIsInstance(self.e.driver, cr_driver.CRDriver, 'Driver type does not resolve to CRDriver type when concurrency is True')

        e = Executor(production=False)
        self.assertIsInstance(e.driver, AbstractDatabaseDriver, 'Driver does not resolve to AbstractDatabaseDriver when concurrency is False')


driver = ContractDriver(db=0)


class DBTests(unittest.TestCase):
    def setUp(self):
        sys.meta_path.append(DatabaseFinder)
        driver.flush()
        contracts = glob.glob('./test_sys_contracts/*.py')
        self.author = 'unittest'
        self.sb = Sandbox()
        self.mpsb = MultiProcessingSandbox()

        self.e = Executor()
        self.e_prod = Executor(production=True)

        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            driver.set_contract(name=name, code=code, author=self.author)

    def tearDown(self):
        self.mpsb.terminate()
        self.e_prod.sandbox.terminate()
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_base_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}

        result = self.sb.execute(self.author, contract_name,
                                 function_name, kwargs)
        self.assertEqual(result, 'Working')

    def test_base_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        self.assertRaises(ImportError, self.sb.execute,
                          *(self.author, contract_name, function_name, kwargs))

    def test_multiproc_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}

        result = self.mpsb.execute(self.author, contract_name,
                                   function_name, kwargs)
        self.assertEqual(result, 'Working')

    def test_multiproc_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        self.assertRaises(ImportError, self.mpsb.execute,
                          *(self.author, contract_name, function_name, kwargs))

    def test_executor_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        result = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(result['result'], 'Working')
        self.assertEqual(result['status_code'], 0)
        self.assertEqual(result['error'], None)

    def test_executor_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        result = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(result['status_code'], 1)
        self.assertIsInstance(result['error'], ImportError)
        self.assertEqual(result['result'], None)

    def test_executor_prod_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(result['result'], 'Working')
        self.assertEqual(result['status_code'], 0)
        self.assertEqual(result['error'], None)

    def test_executor_prod_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(result['status_code'], 1)
        self.assertIsInstance(result['error'], ImportError)
        self.assertEqual(result['result'], None)


# Stub out the Contract Transaction object for use in the unit test
# We will need to write an integration test that passes real contract
# objects, but here is not the place
class ContractTxStub(object):
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.sender = sender
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs

class TestExecutorIntegration(unittest.TestCase):
    def setUp(self):
        e = Executor(metering=False, production=False)



if __name__ == "__main__":
    unittest.main()
