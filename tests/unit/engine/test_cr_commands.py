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

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRContext(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def _new_cmd(self, sbb_idx=0, contract_idx=0, cr_data=None, finalize=False):
        return CRCmdGetSetBase(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                               data=cr_data or self._new_cr_data(sbb_idx=sbb_idx, finalize=finalize))

    def test_add_one_key_to_mod_list(self):
        KEY = 'key_that_was_modified'
        cr_cmd = self._new_cmd()
        cr_cmd.data['getset'].writes[0].add(KEY)

        actual_mods = cr_cmd.data['getset'].writes

        self.assertEqual(len(actual_mods), 1)
        self.assertEqual({KEY}, actual_mods[0])

    def test_add_many_key_to_mod_list(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd = self._new_cmd()
        cr_cmd.data['getset'].writes[0].add(KEY1)
        cr_cmd.data['getset'].writes[0].add(KEY2)

        actual_mods = cr_cmd.data['getset'].writes
        expected_mods = {0: {KEY1, KEY2}}

        self.assertEqual(len(actual_mods), 1)
        self.assertEqual(len(actual_mods[0]), 2)
        self.assertEqual(actual_mods, expected_mods)

    def test_same_keys_to_mod_list(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key1_that_was_modified'
        cr_cmd = self._new_cmd()
        cr_cmd.data['getset'].writes[0].add(KEY1)
        cr_cmd.data['getset'].writes[0].add(KEY2)

        actual_mods = cr_cmd.data['getset'].writes
        expected_mods = {0: {KEY1}}

        self.assertEqual(len(actual_mods), 1)
        self.assertEqual(len(actual_mods[0]), 1)
        self.assertEqual(actual_mods, expected_mods)

    def test_add_keys_from_different_contract(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd1 = self._new_cmd()
        cr_cmd2 = self._new_cmd(contract_idx=1, cr_data=cr_cmd1.data)
        cr_cmd1.data['getset'].writes[0].add(KEY1)
        cr_cmd2.data['getset'].writes[1].add(KEY2)

        # These guys should share the same modification list (since they are from the same sbb idx)
        self.assertEqual(cr_cmd1.data['getset'].writes, cr_cmd2.data['getset'].writes)
        actual_mods = cr_cmd1.data['getset'].writes

        self.assertEqual(len(actual_mods), 2)
        self.assertEqual(len(actual_mods[0]), 1)
        self.assertEqual(len(actual_mods[1]), 1)
        self.assertEqual(actual_mods[0], {KEY1})
        self.assertEqual(actual_mods[1], {KEY2})

    def test_get_mods_for_sbb_idx_many_keys(self):
        KEY1 = 'key1_that_was_modified'
        KEY2 = 'key2_that_was_modified'
        cr_cmd = self._new_cmd()
        cr_cmd.data['getset'].writes[0].add(KEY1)
        cr_cmd.data['getset'].writes[0].add(KEY2)

        actual_mods = cr_cmd.data['getset'].writes
        expected_mods = {0: {KEY1, KEY2}}

        self.assertEqual(actual_mods, expected_mods)

    def test_adds_empty_set_for_contract_with_no_mods(self):
        KEY2 = 'key2_that_was_modified'
        cr_cmd1 = self._new_cmd()
        cr_cmd2 = self._new_cmd(contract_idx=1, cr_data=cr_cmd1.data)
        # cr_cmd2._add_key_to_mod_list(KEY2)
        cr_cmd2.data['getset'].writes[1].add(KEY2)

        # These guys should share the same modification list (since they are from the same sbb idx)
        self.assertEqual(cr_cmd1.data['getset'].writes, cr_cmd2.data['getset'].writes)
        actual_mods = cr_cmd1.data['getset'].writes

        self.assertEqual(len(actual_mods), 1)
        self.assertEqual(len(actual_mods[0]), 0)
        self.assertEqual(len(actual_mods[1]), 1)
        self.assertEqual(actual_mods[0], set())
        self.assertEqual(actual_mods[1], {KEY2})


if __name__ == "__main__":
    unittest.main()
