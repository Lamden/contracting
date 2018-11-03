from seneca.libs.datatypes import *   # This code most be interpretted for the metaclass stuff to get run
from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest


# DEBUG -- TODO DELETE
# from seneca.engine.datatypes_base import RObjectMeta
# print("reads: {}".format(RObjectMeta.))
# END DEBUG

class TestConflictResolution(TestCase):

    def setUp(self):
        self.master = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.working = redis.StrictRedis(host='localhost', port=6379, db=1)
        self._set_rp()

    def tearDown(self):
        self.master.flushdb()
        self.working.flushdb()

    def _set_rp(self, sbb_idx=0, contract_idx=0, finalize=False):
        self.rp = RedisProxy(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                             finalize=finalize)

    def test_basic_set_get(self):
        KEY1, VAL1 = 'k1', 'v1'
        KEY2, VAL2 = 'k2', 'v2'
        NEW_VAL1 = 'v1_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)

        self.rp.set(KEY1, NEW_VAL1)

        actual = self.rp.get(KEY1).decode()

        self.assertEqual(actual, NEW_VAL1)
        self.assertEqual(self.rp.get(KEY2).decode(), VAL2)

        print("All master keys: {}".format(self.master.keys()))
        print("All working keys: {}".format(self.working.keys()))

    def test_all_keys_and_values_for_basic_set_get(self):
        # TODO this test is fragile af. make him more robust?

        KEY1, VAL1 = 'k1', 'v1'
        KEY2, VAL2 = 'k2', 'v2'
        NEW_VAL1 = 'v1_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)

        self.rp.set(KEY1, NEW_VAL1)
        self.rp.get(KEY2)

        expected_master = {'k1': VAL1, 'k2': VAL2}
        expected_working_keys = {'sbb_0_modifications': KEY1, 'sbb_0:modified:k1': NEW_VAL1, 'sbb_0:original:k2': VAL2,
                                 'sbb_0:original:k1': VAL1}

        print("All master keys: {}".format(self.master.keys()))
        print("All working keys: {}".format(self.working.keys()))

        for key, value in expected_master.items():
            actual_value = self.master.get(key).decode()
            self.assertEqual(value, actual_value)

        for key, value in expected_working_keys.items():
            # We must deal with the modification list separately
            if key == 'sbb_0_modifications':
                self.assertEqual(self.working.llen(key), 1)
                self.assertEqual(self.working.lindex(key, 0).decode(), value)
                continue

            actual_value = self.working.get(key).decode()
            self.assertEqual(value, actual_value)

    def test_unimplemented_method_raises_assert(self):
        with self.assertRaises(AssertionError):
            self.rp.this_is_not_implemented('some_key')


if __name__ == "__main__":
    unittest.main()

