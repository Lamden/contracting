from unittest import TestCase
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting.db.encoder import decode
from time import sleep
import asyncio

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
        with open('../integration/test_contracts/erc20_clone.s.py') as f:
            code = f.read()
            self.c.submit(code, name='erc20', metering=False)

        self.c.executor.metering = True

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_orm_rename_hack(self):
        # This hack renames the contract property on its own balances hash to modify the erc20 balances

        token = self.c.get_contract('erc20')

        pre_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        with open('./contracts/hack_tokens.s.py') as f:
            code = f.read()
            self.c.submit(code, name='token_hack')

        post_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        # Assert greater because some of the balance is lost to stamps
        self.assertGreater(pre_hack_balance, post_hack_balance)

    def test_orm_setattr_hack(self):
        # This hack uses setattr instead of direct property access to do the same thing as above

        token = self.c.get_contract('erc20')

        pre_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        with self.assertRaises(Exception):
            with open('./contracts/builtin_hack_token.s.py') as f:
                code = f.read()
                self.c.submit(code, name='token_hack')

            post_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

            # The balance *should not* change between these tests!
            self.assertEqual(pre_hack_balance, post_hack_balance)

    def test_double_spend_if_stamps_run_out(self):
        token = self.c.get_contract('erc20')

        pre_hack_balance_stu = float(str(self.c.get_var("erc20", "balances", arguments=["stu"])))
        pre_hack_balance_colin = float(str(self.c.get_var("erc20", "balances", arguments=["colin"])))

        # Approve the "hack" contract to spend stu's tokens
        tx_amount=10000
        token.approve(amount=tx_amount, to='con_hack', stamps=200)

        with open('./contracts/double_spend_gas_attack.s.py') as f:
            code = f.read()
            self.c.submit(code, name='con_hack', metering=True)

        # Test the double_spend contract
        # - sends the amount of the "allowance" (set in token.approve as 'tx_amount')
        # - calls transfer_from to send from 'stu' to 'colin' as 'con_hack'
        con_hack = self.c.get_contract('con_hack')
        self.c.raw_driver.commit()
        with self.assertRaises(AssertionError):
            # Should fail when stamp_limit of 200 is reached
            con_hack.double_spend(receiver='colin', stamps=200)

        post_hack_balance_stu = float(str(self.c.get_var("erc20", "balances", arguments=["stu"])))
        post_hack_balance_colin = float(str(self.c.get_var("erc20", "balances", arguments=["colin"])))

        # !!! IMPORTANT NODE !!!
        # In the Lamden Implementation there would be a "rollback" of state after the error.
        # Contracting does not do this itself and instead you get the status_code set to 1 and all the tx info returned.

        # Stu's POST balance should be less than the pre balance (less the tx_amount) because stamps were also deducted
        self.assertLess(post_hack_balance_stu, pre_hack_balance_stu + tx_amount)

        # Colin's balance will be + tx_amount
        # Assert greater because some of the balance is lost to stamps
        self.assertEqual(pre_hack_balance_colin + tx_amount, post_hack_balance_colin)


    def test_stamp_fails_when_calling_infinate_loop_from_another_contract(self):
        with open('./contracts/infinate_loop.s.py') as f:
            code = f.read()
            self.c.submit(code, name='infinate_loop')

        with open('./contracts/call_infinate_loop.s.py') as f:
            code = f.read()
            self.c.submit(code, name='call_infinate_loop', metering=True)

        loop = self.c.get_contract('call_infinate_loop')

        with self.assertRaises(AssertionError):
            loop.call()

    def test_constructor_with_infinate_loop_fails(self):
        with self.assertRaises(AssertionError):
            with open('./contracts/constructor_infinate_loop.s.py') as f:
                code = f.read()
                self.c.submit(code, name='constructor_infinate_loop', metering=True)

    def test_infinate_loop_of_writes_undos_everything(self):
        with self.assertRaises(AssertionError):
            with open('./contracts/con_inf_writes.s.py') as f:
                code = f.read()
                self.c.submit(code, name='con_inf_writes', metering=True)

    def test_accessing_variable_on_another_contract(self):
        token = self.c.get_contract('erc20')

        pre_hack_balance_stu = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        try:
            with open('./contracts/import_hash_from_contract.s.py') as f:
                code = f.read()
                self.c.submit(code, name='import_hash_from_contract', metering=False)
        except:
            pass

        post_hack_balance_stu = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        self.assertEqual(pre_hack_balance_stu, post_hack_balance_stu)

    def test_get_set_driver(self):
        # This hack uses setattr instead of direct property access to do the same thing as above

        token = self.c.get_contract('erc20')
        pre_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        #with self.assertRaises(Exception):
        try:
            with open('./contracts/get_set_driver.py') as f:
                code = f.read()
                self.c.submit(code, name='token_hack', metering=False)
        except Exception as err:
            print(err)
            pass

        post_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        print()
        print(post_hack_balance)

        # The balance *should not* change between these tests!
        self.assertEqual(pre_hack_balance, post_hack_balance)

    def test_get_set_driver_2(self):
        # This hack uses setattr instead of direct property access to do the same thing as above

        token = self.c.get_contract('erc20')
        pre_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        #with self.assertRaises(Exception):
        try:
            with open('./contracts/get_set_driver_2.py') as f:
                code = f.read()
                self.c.submit(code, name='token_hack', metering=False)
        except Exception as err:
            print(err)
            pass

        post_hack_balance = self.c.raw_driver.get_var("erc20", "balances", arguments=["stu"])

        print()
        print(post_hack_balance)

        # The balance *should not* change between these tests!
        self.assertEqual(pre_hack_balance, post_hack_balance)