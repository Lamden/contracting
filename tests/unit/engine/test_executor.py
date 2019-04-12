import unittest
from seneca.execution.executor import *

# Import StateProxy and AbstractDatabaseDriver for property type
# assertions for self.e.driver
from seneca.db.driver import AbstractDatabaseDriver


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
        self.assertIsInstance(self.e.driver, StateProxy, 'Driver type does not resolve to StateProxy type when concurrency is True')

        e = Executor(concurrency=False)
        self.assertIsInstance(e.driver, AbstractDatabaseDriver, 'Driver does not resolve to AbstractDatabaseDriver when concurrency is False')

if __name__ == "__main__":
    unittest.main()
