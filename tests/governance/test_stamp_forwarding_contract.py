from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime, Timedelta


class TestStampForwarding(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu', environment={'now': Datetime(2019, 1, 1)})
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract)
        self.c.raw_driver.commit()

        with open('./contracts/stamp_forwarding.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='stamp_forwarding', code=contract)
        self.c.raw_driver.commit()

        self.submission = self.c.get_contract('submission')
        self.stamp_forwarding = self.c.get_contract('stamp_forwarding')

        # submit erc20 clone
        with open('./contracts/simple_vote.s.py') as f:
            code = f.read()
            self.submission.submit_contract(name='simple_vote', code=code, environment={'now': Datetime(2019, 1, 1)})

        self.simple_vote = self.c.get_contract('simple_vote')

    def tearDown(self):
        #self.c.raw_driver.flush()
        pass

    def test_enable(self):
        enabled = self.c.get_var('simple_vote', '__stamps__.enabled')
        self.assertIsNone(enabled)

        self.stamp_forwarding.enable(contract='simple_vote')
        enabled = self.c.get_var('simple_vote', '__stamps__.enabled')

        self.assertTrue(enabled)

    def test_disable(self):
        self.stamp_forwarding.enable(contract='simple_vote')
        enabled = self.c.get_var('simple_vote', '__stamps__.enabled')

        self.assertTrue(enabled)

        self.stamp_forwarding.disable(contract='simple_vote')
        enabled = self.c.get_var('simple_vote', '__stamps__.enabled')
        self.assertIsNone(enabled)

    def test_enable_fails_not_dev(self):
        with self.assertRaises(Exception):
            self.stamp_forwarding.enable(contract='simple_vote', signer='not_stu')

    def test_disable_fails_not_dev(self):
        with self.assertRaises(Exception):
            self.stamp_forwarding.disable(contract='simple_vote', signer='not_stu')

    def test_change_mode_in_list(self):
        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertIsNone(mode)

        self.stamp_forwarding.change_mode(contract='simple_vote', mode='all')

        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertEqual(mode, 'all')

    def test_change_all_modes(self):
        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertIsNone(mode)

        self.stamp_forwarding.change_mode(contract='simple_vote', mode='all')

        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertEqual(mode, 'all')

        self.stamp_forwarding.change_mode(contract='simple_vote', mode='whitelist')

        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertEqual(mode, 'whitelist')

        self.stamp_forwarding.change_mode(contract='simple_vote', mode='blacklist')

        mode = self.c.get_var('simple_vote', '__stamps__.mode')
        self.assertEqual(mode, 'blacklist')

    def test_change_not_in_list_fails(self):
        with self.assertRaises(Exception):
            self.stamp_forwarding.change_mode(contract='simple_vote', mode='not_all')

    def test_change_mode_not_dev_fails(self):
        with self.assertRaises(Exception):
            self.stamp_forwarding.change_mode(contract='simple_vote', mode='all', signer='not_stu')

    def test_add_whitelist(self):
        whitelisted = self.c.get_var('simple_vote', '__stamps__.whitelist.not_stu')
        self.assertIsNone(whitelisted)

        self.stamp_forwarding.add_to_whitelist(contract='simple_vote', address='not_stu')

        whitelisted = self.c.get_var('simple_vote', '__stamps__.whitelist.not_stu')
        self.assertTrue(whitelisted)

    def test_remove_whitelist(self):
        whitelisted = self.c.get_var('simple_vote', '__stamps__.whitelist.not_stu')
        self.assertIsNone(whitelisted)

        self.stamp_forwarding.add_to_whitelist(contract='simple_vote', address='not_stu')

        whitelisted = self.c.get_var('simple_vote', '__stamps__.whitelist.not_stu')
        self.assertTrue(whitelisted)

        self.stamp_forwarding.remove_from_whitelist(contract='simple_vote', address='not_stu')

        whitelisted = self.c.get_var('simple_vote', '__stamps__.whitelist.not_stu')
        self.assertIsNone(whitelisted)

    def test_add_blacklist(self):
        blacklisted = self.c.get_var('simple_vote', '__stamps__.blacklist.not_stu')
        self.assertIsNone(blacklisted)

        self.stamp_forwarding.add_to_blacklist(contract='simple_vote', address='not_stu')

        blacklisted = self.c.get_var('simple_vote', '__stamps__.blacklist.not_stu')
        self.assertTrue(blacklisted)

    def test_remove_blacklist(self):
        blacklisted = self.c.get_var('simple_vote', '__stamps__.blacklist.not_stu')
        self.assertIsNone(blacklisted)

        self.stamp_forwarding.add_to_blacklist(contract='simple_vote', address='not_stu')

        blacklisted = self.c.get_var('simple_vote', '__stamps__.blacklist.not_stu')
        self.assertTrue(blacklisted)

        self.stamp_forwarding.remove_from_blacklist(contract='simple_vote', address='not_stu')

        blacklisted = self.c.get_var('simple_vote', '__stamps__.blacklist.not_stu')
        self.assertIsNone(blacklisted)