from tests.utils import TestExecutor
import seneca

PATH = seneca.__path__[0] + '/../test_contracts/'
AUTHOR = '__lamden_io__'
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

    def test_seeding(self):
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, kwargs={'wallet_id': founder})
        self.assertEqual(seed_amount, res['output'])
        res = self.ex.execute_function('currency', 'exchange_rate', AUTHOR)
        self.assertEqual(1.0, res['output'])

    def test_transfer(self):
        res = self.ex.execute_function('currency', 'transfer', wallets[0], kwargs={'to': wallets[1], 'amount': 100})
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[0]})
        self.assertEqual(seed_amount-100, res['output'])
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[1]})
        self.assertEqual(seed_amount+100, res['output'])

    def test_approve(self):
        res = self.ex.execute_function('currency', 'approve', wallets[0], kwargs={'spender': wallets[1], 'amount': 100})
        res = self.ex.execute_function('currency', 'allowance', wallets[0], kwargs={'approver': wallets[0], 'spender': wallets[1]})
        self.assertEqual(res['output'], 100)

    def test_transfer_from(self):
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[1]})
        original_balance = res['output']
        res = self.ex.execute_function('currency', 'approve', wallets[0],
                                       kwargs={'spender': wallets[1], 'amount': 100})
        res = self.ex.execute_function('currency', 'transfer_from', wallets[1],
                                       kwargs={'approver': wallets[0], 'amount': 100})
        res = self.ex.execute_function('currency', 'allowance', wallets[0], kwargs={'approver': wallets[0], 'spender': wallets[1]})
        self.assertEqual(res['output'], 0)
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[1]})
        self.assertEqual(res['output'], original_balance+100)

    def test_unavailable_allowance(self):
        with self.assertRaises(AssertionError):
            res = self.ex.execute_function('currency', 'transfer_from', 'stu', kwargs={
                'approver': 'davis', 'amount': 123
            })

    def test_too_large_custodial_spend(self):
        res = self.ex.execute_function('currency', 'approve', wallets[0], kwargs={'spender': wallets[1], 'amount': 100})
        with self.assertRaises(AssertionError):
            res = self.ex.execute_function('currency', 'transfer_from', wallets[1], kwargs={
                'approver': wallets[0], 'amount': 500
            })