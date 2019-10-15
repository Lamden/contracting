import unittest
from contracting.execution.executor import Sandbox, Executor, MultiProcessingSandbox
import sys
import glob
# Import ContractDriver and AbstractDatabaseDriver for property type
# assertions for self.e._driver
from contracting.db.driver import AbstractDatabaseDriver, ContractDriver
from contracting.execution.module import DatabaseFinder
from contracting.compilation.compiler import ContractingCompiler
from contracting.db.cr.transaction_bag import TransactionBag

driver = ContractDriver(db=0)


class DBTests(unittest.TestCase):
    def setUp(self):
        sys.meta_path.append(DatabaseFinder)
        driver.flush()
        contracts = glob.glob('./test_sys_contracts/*.py')
        self.author = b'unittest'
        self.sb = Sandbox()
        self.mpsb = MultiProcessingSandbox()

        self.e = Executor(metering=False)

        compiler = ContractingCompiler()

        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            new_code = compiler.parse_to_code(code, lint=False)

            driver.set_contract(name=name, code=new_code)
            driver.commit()

    def tearDown(self):
        self.mpsb.terminate()
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_base_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}

        status_code, result, _ = self.sb.execute(self.author, contract_name,
                                              function_name, kwargs)
        self.assertEqual(result, 'Working')

    def test_base_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result, _ = self.sb.execute(self.author, contract_name, function_name, kwargs)

        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)

    def test_base_execute_bag(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        input_hash = 'A'*64

        tx = ContractTxStub(self.author, contract_name, function_name, kwargs)
        txbag = TransactionBag([tx], input_hash, 0, completion_handler_stub)

        results = self.sb.execute_bag(txbag)

        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[0][1], 'Working')

    def test_executor_execute(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result, stamps = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(result, 'Working')
        self.assertEqual(status_code, 0)

    def test_executor_execute_fail(self):
        contract_name = 'badmodule'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        status_code, result, stamp = self.e.execute(self.author, contract_name,
                                             function_name, kwargs)
        self.assertEqual(status_code, 1)
        self.assertIsInstance(result, ImportError)

    def test_executor_execute_bag(self):
        contract_name = 'module_func'
        function_name = 'test_func'
        kwargs = {'status': 'Working'}
        input_hash = 'A'*64

        tx = ContractTxStub(self.author, contract_name, function_name, kwargs)
        txbag = TransactionBag([tx], input_hash, 0, completion_handler_stub)

        results = self.e.execute_bag(txbag)

        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[0][1], 'Working')


# Stub out the Contract Transaction object for use in the unit test
# We will need to write an integration test that passes real contract
# objects, but here is not the place
class PayloadStub:
    def __init__(self, sender, contract_name, func_name, kwargs, stampsSupplied=1000000):
        self.sender = sender
        self.contractName = contract_name
        self.functionName = func_name
        self.kwargs = kwargs
        self.stampsSupplied = stampsSupplied


class ContractTxStub:
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender, contract_name, func_name, kwargs)

def completion_handler_stub():
    pass


class TestExecutorIntegration(unittest.TestCase):
    def setUp(self):
        e = Executor(metering=False, production=False)



if __name__ == "__main__":
    unittest.main()
