from unittest import TestCase
from contracting.client import ContractingClient


class TestMembers(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()

        f = open('./contracts/currency.s.py')
        self.client.submit(f.read(), 'currency')
        f.close()

        f = open('./contracts/foundation.s.py')
        self.client.submit(f.read(), 'foundation', constructor_args={
            'vk': 'test'
        })
        f.close()

        self.foundation = self.client.get_contract('foundation')
        self.currency = self.client.get_contract('currency')

    def test_withdraw(self):
        # Send money to foundation
        self.currency.transfer(amount=10000, to='foundation')

        self.foundation.withdraw(amount=123, signer='test')

        self.assertEqual(self.currency.balances['test'], 123)

    def test_change_owner(self):
        self.currency.transfer(amount=10000, to='foundation')

        self.foundation.change_owner(vk='xxx', signer='test')

        with self.assertRaises(AssertionError):
            self.foundation.withdraw(amount=123, signer='test')

        self.foundation.withdraw(amount=123, signer='xxx')
        self.assertEqual(self.currency.balances['xxx'], 123)

    def test_change_owner_fails_if_not_owner(self):
        with self.assertRaises(AssertionError):
            self.foundation.change_owner(vk='xxx', signer='yyy')
