import unittest
from seneca.execution.executor import Sandbox, Executor, MultiProcessingSandbox
import sys
import glob
# Import ContractDriver and AbstractDatabaseDriver for property type
# assertions for self.e.driver
from seneca.db.driver import AbstractDatabaseDriver, ContractDriver
from seneca.execution.module import DatabaseFinder


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
            driver.commit()

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
        status_code, result = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_executor_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)

    def test_executor_prod_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_executor_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)

    def test_executor_prod_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_executor_prod_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)

    def test_executor_prod_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_executor_prod_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result = self.e_prod.execute(self.author, contract_name,
                                                  function_name, kwargs)
        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)


class TestBag():
    def test_executor_execute_bag(self):
        ctx1 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Working'})
        ctx2 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Also Working'})
        bag = [ctx1, ctx2]
        results = self.e.execute_bag(bag)

        # Assert the status codes in the results object are correct
        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[1][0], 0)

        # Assert the response objects in the results are correct and
        # in the correct order
        self.assertEqual(results[0][1], 'Working')
        self.assertEqual(results[1][1], 'Also Working')

    def test_executor_execute_bag_fail(self):
        ctx1 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Working'})
        ctx2 = ContractTxStub(self.author, 'badmodule', 'test_func',
                              {'status': 'Also Working'})
        bag = [ctx1, ctx2]
        results = self.e.execute_bag(bag)

        # Assert the status codes in the results object are correct
        self.assertEqual(results[0][0], 0)
        # Second result for ctx2 should be failure
        self.assertEqual(results[1][0], 1)

        # Assert the response objects in the results are correct and
        # in the correct order
        self.assertEqual(results[0][1], 'Working')
        # Assert we get the correct error on the failing ctx
        self.assertIsInstance(results[1][1], ImportError)

    def test_executor_prod_execute_bag(self):
        ctx1 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Working'})
        ctx2 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Also Working'})
        bag = [ctx1, ctx2]
        results = self.e_prod.execute_bag(bag)

        # Assert the status codes in the results object are correct
        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[1][0], 0)

        # Assert the response objects in the results are correct and
        # in the correct order
        self.assertEqual(results[0][1], 'Working')
        self.assertEqual(results[1][1], 'Also Working')

    def test_executor_prod_execute_bag_fail(self):
        ctx1 = ContractTxStub(self.author, 'module_func', 'test_func',
                              {'status': 'Working'})
        ctx2 = ContractTxStub(self.author, 'badmodule', 'test_func',
                              {'status': 'Also Working'})
        bag = [ctx1, ctx2]
        results = self.e_prod.execute_bag(bag)

        # Assert the status codes in the results object are correct
        self.assertEqual(results[0][0], 0)
        # Second result for ctx2 should be failure
        self.assertEqual(results[1][0], 1)

        # Assert the response objects in the results are correct and
        # in the correct order
        self.assertEqual(results[0][1], 'Working')
        # Assert we get the correct error on the failing ctx
        self.assertIsInstance(results[1][1], ImportError)


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
