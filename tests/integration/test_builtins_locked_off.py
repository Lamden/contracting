from unittest import TestCase
from contracting.client import ContractingClient
from contracting.execution.executor import Executor


class TestBuiltinsLockedOff(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu', executor=Executor(production=True))

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_if_builtin_can_be_submitted(self):
        with open('./test_contracts/builtin_lib.s.py') as f:
            contract = f.read()

        with self.assertRaises(ImportError):
            self.c.submit(contract, name='builtin')

    def test_if_non_builtin_can_be_submitted(self):
        pass