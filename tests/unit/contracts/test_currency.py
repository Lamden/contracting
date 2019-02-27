from tests.utils import TestExecutor
import seneca
from os.path import join, dirname
import numpy

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

    def setUp(self):
        super().setUp()
        with open(join(PATH, 'new_currency.sen.py')) as f:
            self.ex.execute_function('smart_contract', 'submit_contract', AUTHOR, kwargs={
                'contract_name': 'new_currency',
                'code_str': f.read()
            })

    def test_seeding(self):
        res = self.ex.execute_function('new_currency', 'balance_of', AUTHOR, kwargs={'wallet_id': founder})
        self.assertEqual(seed_amount, res['output'])
        res = self.ex.execute_function('new_currency', 'exchange_rate', AUTHOR)
        self.assertEqual(1.0, res['output'])

    def test_transfer(self):
        res = self.ex.execute_function('new_currency', 'transfer', wallets[0], kwargs={'to': wallets[1], 'amount': 100})
        res = self.ex.execute_function('new_currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[0]})
        self.assertEqual(seed_amount-100, res['output'])
        res = self.ex.execute_function('new_currency', 'balance_of', AUTHOR, kwargs={'wallet_id': wallets[1]})
        self.assertEqual(seed_amount+100, res['output'])

    def test_approve(self):
        res = self.ex.execute_function('new_currency', 'approve', wallets[0], kwargs={'spender': wallets[1], 'amount': 100})
        res = self.ex.execute_function('new_currency', 'approve', wallets[0], kwargs={'spender': wallets[2], 'amount': 100})
        res = self.ex.execute_function('new_currency', 'approve', wallets[0], kwargs={'spender': wallets[3], 'amount': 100})
        res = self.ex.execute_function('new_currency', 'allowance', wallets[0], kwargs={'approver': wallets[0], 'spender': wallets[1]})
        self.assertEqual(res['output'], 100)
