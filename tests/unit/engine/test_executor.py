import unittest
from seneca.execution.executor import Sandbox, Executor, MultiProcessingSandbox
import sys
import glob
# Import StateProxy and AbstractDatabaseDriver for property type
# assertions for self.e.driver
from seneca.db.driver import AbstractDatabaseDriver, ContractDriver
from seneca.execution.module import DatabaseFinder


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.e = Executor()

    def tearDown(self):
        del self.e

    def test_init(self):
        self.assertEqual(self.e.concurrency, True, 'Concurrency not set to True by default.')
        self.assertEqual(self.e.metering, True, 'Metering not set to true by default.')

    def test_dynamic_init(self):
        e = Executor(metering=False, concurrency=False)

        self.assertEqual(e.metering, False, 'Metering is not set to false after dynamic set')
        self.assertEqual(e.concurrency, False, 'Concurrency is not set to false after dynamic set.')

    def test_driver_resolution(self):
        # The StateProxy class is not able to be isolated so this test is turned off for now
        # Colin TODO: Discuss with Davis how we update StateProxy (or isolate the concept)
        #self.assertIsInstance(self.e.driver, conflict_resolution.StateProxy, 'Driver type does not resolve to StateProxy type when concurrency is True')

        e = Executor(concurrency=False)
        self.assertIsInstance(e.driver, AbstractDatabaseDriver, 'Driver does not resolve to AbstractDatabaseDriver when concurrency is False')


driver = ContractDriver(db=0)


class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        self.author = 'unittest'

    def test_execute(self):
        code = '''b = 10'''
        output, env = self.sb.execute('unittest', code)
        self.assertEqual(env['b'], 10)


class TestMultiProcessingSandbox(unittest.TestCase):
    def setUp(self):
        self.sb = MultiProcessingSandbox()
        self.author = 'unittest'

    def tearDown(self):
        self.sb.terminate()

    def test_execute(self):
        code = '''b = 10'''
        output, env = self.sb.execute('unittest', code)
        self.assertEqual(env['b'], 10)


class TestSandboxWithDB(unittest.TestCase):
    def setUp(self):
        sys.meta_path.append(DatabaseFinder)
        driver.flush()
        contracts = glob.glob('./test_sys_contracts/*.py')
        self.author = 'unittest'
        self.code = '''import module1
import sys
print("now i can run my functions!")
a = 6
'''
        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            driver.set_contract(name=name, code=code, author=self.author)

    def tearDown(self):
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_base_execute(self):
        sb = Sandbox()
        output, env = sb.execute(self.author, self.code)
        self.assertEqual(env['a'], 6)

    def test_multiproc_execute(self):
        sb = MultiProcessingSandbox()
        output, env = sb.execute(self.author, self.code)
        self.assertEqual(env['a'], 6)
        sb.terminate()


if __name__ == "__main__":
    unittest.main()
