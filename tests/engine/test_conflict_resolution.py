from seneca.libs.datatypes import *   # This code most be interpretted for the metaclass stuff to get run
from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest


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
                             data=self._new_cr_data(sbb_idx, finalize), finalize=finalize)

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRDataContainer(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

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

    def test_all_keys_and_values_for_basic_set_get(self):
        # TODO this test is fragile af. make him more robust?

        KEY1, VAL1 = 'k1', b'v1'
        KEY2, VAL2 = 'k2', b'v2'
        KEY3, VAL3 = 'k3', b'v3'
        NEW_VAL1 = b'v1_NEW'
        NEW_VAL3 = b'v3_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)
        self.master.set(KEY3, b'val 3 on master that should be ignored in presence of KEY3 on common layer')
        self.working.set(KEY3, VAL3)

        self.rp.set(KEY1, NEW_VAL1)
        self.rp.get(KEY2)  # To trigger a copy to sbb specific layer
        self.rp.set(KEY3, NEW_VAL3)  # To trigger a copy to sbb specific layer

        # Check the modified and original values
        getset = self.rp.data['getset']
        k1_expected = {'og': VAL1, 'mod': NEW_VAL1}
        k2_expected = {'og': VAL2, 'mod': None}
        k3_expected = {'og': VAL3, 'mod': NEW_VAL3}
        self.assertEqual(getset[KEY1], k1_expected)
        self.assertEqual(getset[KEY2], k2_expected)
        self.assertEqual(getset[KEY3], k3_expected)

        # Check modifications list
        expected_mods = [{KEY1, KEY3}]
        self.assertEqual(self.rp.data['getset'].mods, expected_mods)

    def test_unimplemented_method_raises_assert(self):
        with self.assertRaises(AssertionError):
            self.rp.this_is_not_implemented('some_key')


if __name__ == "__main__":
    unittest.main()

