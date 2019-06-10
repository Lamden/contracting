from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


class TestDynamicImports(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract, author='sys')

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./test_contracts/stubucks.s.py') as f:
            code = f.read()
            submission.submit_contract(name='stubucks', code=code)

        with open('./test_contracts/tejastokens.s.py') as f:
            code = f.read()
            submission.submit_contract(name='tejastokens', code=code)

        with open('./test_contracts/bastardcoin.s.py') as f:
            code = f.read()
            submission.submit_contract(name='bastardcoin', code=code)

        with open('./test_contracts/dynamic_importing.s.py') as f:
            code = f.read()
            submission.submit_contract(name='dynamic_importing', code=code)

        self.stubucks = self.c.get_contract('stubucks')
        self.tejastokens = self.c.get_contract('tejastokens')
        self.bastardcoin = self.c.get_contract('bastardcoin')
        self.dynamic_importing = self.c.get_contract('dynamic_importing')

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_successful_submission(self):
        self.assertEqual(self.stubucks.balance_of(account='stu'), 123)
        self.assertEqual(self.stubucks.balance_of(account='colin'), 321)

        self.assertEqual(self.tejastokens.balance_of(account='stu'), 321)
        self.assertEqual(self.tejastokens.balance_of(account='colin'), 123)

        self.assertEqual(self.bastardcoin.balance_of(account='stu'), 999)
        self.assertEqual(self.bastardcoin.balance_of(account='colin'), 555)

    def test_get_stubuck_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='stubucks', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='stubucks', account='colin')

        self.assertEqual(stu, 123)
        self.assertEqual(colin, 321)

    def test_get_tejastokens_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='tejastokens', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='tejastokens', account='colin')

        self.assertEqual(stu, 321)
        self.assertEqual(colin, 123)

    def test_get_bastardcoin_balances(self):
        stu = self.dynamic_importing.balance_for_token(tok='bastardcoin', account='stu')
        colin = self.dynamic_importing.balance_for_token(tok='bastardcoin', account='colin')

        self.assertEqual(stu, 999)
        self.assertEqual(colin, 555)

    def test_is_erc20(self):
        self.assertTrue(self.dynamic_importing.is_erc20_compatible(tok='stubucks'))
        self.assertTrue(self.dynamic_importing.is_erc20_compatible(tok='tejastokens'))
        self.assertFalse(self.dynamic_importing.is_erc20_compatible(tok='bastardcoin'))

    def test_get_balances_erc20_enforced_stubucks(self):
        stu = self.dynamic_importing.only_erc20(tok='stubucks', account='stu')
        colin = self.dynamic_importing.only_erc20(tok='stubucks', account='colin')

        self.assertEqual(stu, 123)
        self.assertEqual(colin, 321)

    def test_get_balances_erc20_enforced_tejastokens(self):
        stu = self.dynamic_importing.only_erc20(tok='tejastokens', account='stu')
        colin = self.dynamic_importing.only_erc20(tok='tejastokens', account='colin')

        self.assertEqual(stu, 321)
        self.assertEqual(colin, 123)

    def test_erc20_enforced_fails_for_bastardcoin(self):
        with self.assertRaises(AssertionError):
            stu = self.dynamic_importing.only_erc20(tok='bastardcoin', account='stu')
