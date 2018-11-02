from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest



class TestCRCommandsBase(TestCase):

    def setUp(self):
        self.master = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.working = redis.StrictRedis(host='localhost', port=6379, db=1)

    def tearDown(self):
        self.master.flushdb()
        self.working.flushdb()

    def test_add_one_key_to_mod_list(self):
        KEY = 'key_that_was_modified'
        cr_cmd = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd._add_key_to_mod_list(KEY)

        mods_key = cr_cmd._mods_list_key
        actual_mods = self.working.lindex(mods_key, 0).decode()

        self.assertEqual(self.working.llen(mods_key), 1)
        self.assertEqual(KEY, actual_mods)

    def test_diff_sublocks_diff_mod_keys(self):
        cr_cmd1 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd2 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=1, contract_idx=0)

        self.assertNotEqual(cr_cmd1._mods_list_key, cr_cmd2._mods_list_key)

    def test_add_many_key_to_mod_list(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd._add_key_to_mod_list(KEY1)
        cr_cmd._add_key_to_mod_list(KEY2)

        mods_key = cr_cmd._mods_list_key
        actual_mods = self.working.lindex(mods_key, 0).decode()
        expected_mods = KEY1 + CRCommandBase.MODS_LIST_DELIM + KEY2

        self.assertEqual(self.working.llen(mods_key), 1)
        self.assertEqual(actual_mods, expected_mods)

    def test_same_keys_to_mod_list(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key1_that_was_modified'
        cr_cmd = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd._add_key_to_mod_list(KEY1)
        cr_cmd._add_key_to_mod_list(KEY2)

        mods_key = cr_cmd._mods_list_key
        actual_mods = self.working.lindex(mods_key, 0).decode()
        expected_mods = KEY1

        self.assertEqual(self.working.llen(mods_key), 1)
        self.assertEqual(actual_mods, expected_mods)

    def test_add_keys_from_different_contract(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd1 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd2 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=1)
        cr_cmd1._add_key_to_mod_list(KEY1)
        cr_cmd2._add_key_to_mod_list(KEY2)

        mods_key1 = cr_cmd1._mods_list_key
        mods_key2 = cr_cmd2._mods_list_key

        # They should have the same key for mods list (since they are in the same sb they are writing to same list)
        self.assertEqual(mods_key1, mods_key2)

        actual_mods1 = self.working.lindex(mods_key1, 0).decode()
        actual_mods2 = self.working.lindex(mods_key2, 1).decode()

        self.assertEqual(self.working.llen(mods_key1), 2)
        self.assertEqual(actual_mods1, KEY1)
        self.assertEqual(actual_mods2, KEY2)

    def test_get_mods_for_sbb_idx_one_key(self):
        KEY = 'key_that_was_modified'
        cr_cmd = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd._add_key_to_mod_list(KEY)

        actual_mods = CRCommandBase.get_mods_for_sbb_idx(0, self.working)
        expected_mods = [[KEY]]

        self.assertEqual(actual_mods, expected_mods)

    def test_get_mods_for_sbb_idx_many_keys(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd._add_key_to_mod_list(KEY1)
        cr_cmd._add_key_to_mod_list(KEY2)

        actual_mods = CRCommandBase.get_mods_for_sbb_idx(0, self.working)
        expected_mods = [[KEY1, KEY2]]

        self.assertEqual(actual_mods, expected_mods)

    def test_get_mods_for_sbb_idx_differnt_contracts_many_keys(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        KEY3 = 'key3_that_was_modified'
        KEY4 = 'key4_that_was_modified'
        cr_cmd1 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        cr_cmd2 = CRCommandBase(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=1)
        cr_cmd1._add_key_to_mod_list(KEY1)
        cr_cmd1._add_key_to_mod_list(KEY2)
        cr_cmd2._add_key_to_mod_list(KEY3)
        cr_cmd2._add_key_to_mod_list(KEY4)

        actual_mods = CRCommandBase.get_mods_for_sbb_idx(0, self.working)
        expected_mods = [[KEY1, KEY2], [KEY3, KEY4]]

        self.assertEqual(actual_mods, expected_mods)


if __name__ == "__main__":
    unittest.main()

