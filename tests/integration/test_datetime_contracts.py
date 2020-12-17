from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime


class TestSenecaClientReplacesExecutor(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

        with open('test_contracts/dater.py') as f:
            self.c.submit(f=f.read(), name='dater')

        self.dater = self.c.get_contract('dater')

    def tearDown(self):
        self.c.flush()

    def test_datetime_passed_argument_and_now_are_correctly_compared(self):
        self.dater.replicate(d=Datetime(year=3000, month=1, day=1))

    def test_datetime_passed_argument_and_now_are_correctly_compared_json(self):
        with self.assertRaises(TypeError):
            self.dater.replicate(d={'__time__':[3000, 12, 15, 12, 12, 12, 0]})

        with self.assertRaises(TypeError):
            self.dater.replicate(d=[2025, 11, 15, 21, 47, 14, 0])
