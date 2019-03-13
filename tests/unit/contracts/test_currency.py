from tests.utils import TestExecutor
import seneca
from decimal import Decimal

PATH = seneca.__path__[0] + '/../test_contracts/'
AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
founder_wallets = wallets = [
    '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502',
    'a103715914a7aae8dd8fddba945ab63a169dfe6e37f79b4a58bcf85bfd681694',
    '20da05fdba92449732b3871cc542a058075446fedb41430ee882e99f9091cc4d',
    'ed19061921c593a9d16875ca660b57aa5e45c811c8cf7af0cfcbd23faa52cbcd',
    'cb9bfd4b57b243248796e9eb90bc4f0053d78f06ce68573e0fdca422f54bb0d2',
    'c1f845ad8967b93092d59e4ef56aef3eba49c33079119b9c856a5354e9ccdf84'
]
founder = founder_wallets[0]
seed_amount = 1000000


class TestCurrency(TestExecutor):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.balances = cls.ex.get_resource('currency', 'balances')
        cls.xrate = cls.ex.get_resource('currency', 'xrate')
        cls.allowed = cls.ex.get_resource('currency', 'allowed')

    def test_seeding(self):
        self.assertEqual(seed_amount, self.balances[founder])
        self.assertEqual(1.0, self.xrate)

    def test_transfer(self):
        res = self.ex.execute_function('currency', 'transfer', wallets[0], kwargs={'to': wallets[1], 'amount': 100})
        self.assertEqual(seed_amount-100, self.balances[wallets[0]])
        self.assertEqual(seed_amount+100, self.balances[wallets[1]])

    def test_approve(self):
        res = self.ex.execute_function('currency', 'approve', wallets[0], kwargs={'spender': wallets[1], 'amount': 100})
        self.assertEqual(self.allowed[wallets[0]][wallets[1]], 100)

    def test_transfer_from(self):
        original_balance = Decimal(self.balances[wallets[1]])
        res = self.ex.execute_function('currency', 'approve', wallets[0],
                                       kwargs={'spender': wallets[1], 'amount': 100})
        res = self.ex.execute_function('currency', 'transfer_from', wallets[1],
                                       kwargs={'approver': wallets[0], 'spender': wallets[1], 'amount': 100})
        self.assertEqual(self.allowed[wallets[0]][wallets[1]], 0)
        self.assertEqual(self.balances[wallets[1]], original_balance+100)

    def test_unavailable_allowance(self):
        with self.assertRaises(AssertionError):
            res = self.ex.execute_function('currency', 'transfer_from', 'stu', kwargs={
                'approver': 'davis', 'spender': wallets[1], 'amount': 123
            })

    def test_too_large_custodial_spend(self):
        self.ex.execute_function('currency', 'approve', wallets[0], kwargs={'spender': wallets[1], 'amount': 100})
        with self.assertRaises(AssertionError):
            self.ex.execute_function('currency', 'transfer_from', wallets[1], kwargs={
                'approver': wallets[0], 'spender': wallets[1], 'amount': 500
            })