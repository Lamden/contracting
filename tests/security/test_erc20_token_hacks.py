from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient


class TestTokenHacks(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract)

        self.c.raw_driver.commit()

        self.c.executor.currency_contract = 'erc20'
        self.c.signer = 'stu'

        # submit erc20 clone
        with open('./contracts/erc20.s.py') as f:
            code = f.read()
            self.c.submit(code, name='erc20', metering=False)

        self.c.executor.metering = True

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_orm_rename_hack(self):
        # This hack renames the contract property on its own balances hash to modify the erc20 balances

        token = self.c.get_contract('erc20')

        pre_hack_balance = token.balances['stu']

        with open('./contracts/hack_tokens.s.py') as f:
            code = f.read()
            self.c.submit(code, name='token_hack')

        post_hack_balance = token.balances['stu']

        # Assert greater because some of the balance is lost to stamps
        self.assertGreater(pre_hack_balance, post_hack_balance)

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

    def test_double_spend_if_stamps_run_out(self):
        token = self.c.get_contract('erc20')

        pre_hack_balance_stu = token.balances['stu']
        pre_hack_balance_colin = token.balances['colin']

        token.approve(amount=10000, to='hack')

        with open('./contracts/double_spend_gas_attack.s.py') as f:
            code = f.read()
            self.c.submit(code, name='hack', metering=True)

        hack = self.c.get_contract('hack')
        try:
            hack.double_spend(reciever='colin')
        except:
            pass

        post_hack_balance_stu = token.balances['stu']
        post_hack_balance_colin = token.balances['colin']

        # Assert greater because some of the balance is lost to stamps
        self.assertGreater(pre_hack_balance_stu, post_hack_balance_stu)

        # Colin balance is not affected because it was the recipient of tokens
        self.assertEqual(pre_hack_balance_colin, post_hack_balance_colin)

    def test_stamp_fails_when_calling_infinate_loop_from_another_contract(self):
        with open('./contracts/infinate_loop.s.py') as f:
            code = f.read()
            self.c.submit(code, name='infinate_loop')

        with open('./contracts/call_infinate_loop.s.py') as f:
            code = f.read()
            self.c.submit(code, name='call_infinate_loop', metering=False)

        loop = self.c.get_contract('call_infinate_loop')

        with self.assertRaises(AssertionError):
            loop.call()

    def test_constructor_with_infinate_loop_fails(self):
        with self.assertRaises(AssertionError):
            with open('./contracts/constructor_infinate_loop.s.py') as f:
                code = f.read()
                self.c.executor.execute(

                )
                self.c.submit(code, name='constructor_infinate_loop')

    def test_infinate_loop_of_writes_undos_everything(self):
        with self.assertRaises(AssertionError):
            with open('./contracts/con_inf_writes.s.py') as f:
                code = f.read()
                self.c.submit(code, name='con_inf_writes')

    def test_accessing_variable_on_another_contract(self):
        token = self.c.get_contract('erc20')

        pre_hack_balance_stu = token.balances['stu']

        try:
            with open('./contracts/import_hash_from_contract.s.py') as f:
                code = f.read()
                self.c.submit(code, name='import_hash_from_contract', metering=False)
        except:
            pass

        post_hack_balance_stu = token.balances['stu']

        self.assertEqual(pre_hack_balance_stu, post_hack_balance_stu)
