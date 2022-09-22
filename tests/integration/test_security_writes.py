from contracting.client import ContractingClient
from unittest import TestCase


def exploit():
    @construct
    def seed():
        key = 'currency.balances:' + ctx.caller
        rt.env.get('__Driver').driver.set(key, 100000000000)

    @export
    def a():
        return 1


class TestExploit(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()

    def tearDown(self):
        self.c.flush()

    def test_coin_construction(self):
        with self.assertRaises(Exception):
            self.c.submit(exploit)
