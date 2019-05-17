from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


class TestTokenHacks(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract, author='sys')

        self.c.raw_driver.commit()

        # submit erc20 clone
        with open('./contracts/erc20.s.py') as f:
            code = f.read()
            self.c.submit(code, name='erc20')

    def tearDown(self):
        #self.c.raw_driver.flush()
        pass

    def test_orm_rename_hack(self):
        # This hack renames the contract property on its own balances hash to modify the erc20 balances

        token = self.c.get_contract('erc20')

        pre_hack_balance = token.balances['stu']

        with open('./contracts/hack_tokens.s.py') as f:
            code = f.read()
            self.c.submit(code, name='token_hack')

        post_hack_balance = token.balances['stu']

        # The balance *should not* change between these tests!
        self.assertEqual(pre_hack_balance, post_hack_balance)

    def test_orm_setattr_hack(self):
        # This hack uses setattr instead of direct property access to do the same thing as above

        token = self.c.get_contract('erc20')

        pre_hack_balance = token.balances['stu']

        with self.assertRaises(Exception):
            with open('./contracts/builtin_hack_token.s.py') as f:
                code = f.read()
                self.c.submit(code, name='token_hack')

            post_hack_balance = token.balances['stu']

            # The balance *should not* change between these tests!
            self.assertEqual(pre_hack_balance, post_hack_balance)