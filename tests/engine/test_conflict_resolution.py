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
        self.sbb_data = {}
        self._set_rp()

    def tearDown(self):
        self.master.flushdb()
        self.working.flushdb()

    def _set_rp(self, sbb_idx=0, contract_idx=0, finalize=False):
        if contract_idx in self.sbb_data:
            data = self.sbb_data[contract_idx]
        else:
            data = self._new_cr_data(sbb_idx=sbb_idx, finalize=finalize)
            self.sbb_data[contract_idx] = data

        self.r = RedisProxy(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                            data=data)

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRDataContainer(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def test_basic_set_get(self):
        KEY1, VAL1 = 'k1', 'v1'
        KEY2, VAL2 = 'k2', 'v2'
        NEW_VAL1 = 'v1_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)

        self.r.set(KEY1, NEW_VAL1)

        actual = self.r.get(KEY1).decode()

        self.assertEqual(actual, NEW_VAL1)
        self.assertEqual(self.r.get(KEY2).decode(), VAL2)

        self.assertTrue(self.sbb_data[0]['getset'].should_rerun(0))
        self.assertFalse(self.sbb_data[0]['getset'].should_rerun(1))

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

        self.r.set(KEY1, NEW_VAL1)
        self.r.contract_idx = 2
        self.r.get(KEY2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.set(KEY3, NEW_VAL3)  # To trigger a copy to sbb specific layer

        # Check the modified and original values
        getset = self.r.data['getset']
        k1_expected = {'og': VAL1, 'mod': NEW_VAL1}
        k2_expected = {'og': VAL2, 'mod': None}
        k3_expected = {'og': VAL3, 'mod': NEW_VAL3}
        self.assertEqual(getset[KEY1], k1_expected)
        self.assertEqual(getset[KEY2], k2_expected)
        self.assertEqual(getset[KEY3], k3_expected)

        # Check modifications list
        expected_mods = [{KEY1}, set(), {KEY3}]
        self.assertEqual(self.r.data['getset'].mods, expected_mods)

        # Check should_rerun (tinker with common first)
        self.working.set(KEY1, b'A NEW VALUE HAS ARRIVED')
        self.working.set(KEY2, b'A NEW VALUE HAS ARRIVED AGAIN')
        self.assertTrue(self.sbb_data[0].should_rerun(0))
        self.assertFalse(self.sbb_data[0].should_rerun(1))
        self.assertFalse(self.sbb_data[0].should_rerun(2))

        # Check merge_to_master
        cr_data = self.sbb_data[0]
        cr_data.merge_to_master()
        self.assertEqual(self.master.get(KEY1), NEW_VAL1)
        self.assertEqual(self.master.get(KEY2), VAL2)
        self.assertEqual(self.master.get(KEY3), NEW_VAL3)

        # Check state
        expected_state = "SET {k1};b'{v1};SET {k2};b'{v2}SET;{k3};b'{v3}"\
                         .format(k1=KEY1, v1=NEW_VAL1, k2=KEY2, v2=VAL2, k3=KEY3, v3=VAL3)

    def test_merge_to_master(self):
        # TODO this test is fragile af. make him more robust?

        KEY1, VAL1 = 'k1', b'v1'
        KEY2, VAL2 = 'k2', b'v2'
        KEY3, VAL3 = 'k3', b'v3'
        KEY4, VAL4 = 'k4', b'v4'
        NEW_VAL1 = b'v1_NEW'
        NEW_VAL3 = b'v3_NEW'
        NEW_VAL4 = b'v4_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)
        self.master.set(KEY3, b'val 3 on master that should be ignored in presence of KEY3 on common layer')
        self.working.set(KEY3, VAL3)

        self.r.set(KEY1, NEW_VAL1)
        self.r.contract_idx = 2
        self.r.get(KEY2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.set(KEY3, NEW_VAL3)
        self.r.set(KEY4, NEW_VAL4)

        # Check merge_to_master
        cr_data = self.sbb_data[0]
        cr_data.merge_to_master()
        self.assertEqual(self.master.get(KEY1), NEW_VAL1)
        self.assertEqual(self.master.get(KEY2), VAL2)
        self.assertEqual(self.master.get(KEY3), NEW_VAL3)
        self.assertEqual(self.master.get(KEY4), NEW_VAL4)

    def test_state_rep(self):
        # TODO this test is fragile af. make him more robust?

        KEY1, VAL1 = 'k1', b'v1'
        KEY2, VAL2 = 'k2', b'v2'
        KEY3, VAL3 = 'k3', b'v3'
        KEY4, VAL4 = 'k4', b'v4'
        NEW_VAL1 = b'v1_NEW'
        NEW_VAL3 = b'v3_NEW'
        NEW_VAL4 = b'v4_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)
        self.master.set(KEY3, b'val 3 on master that should be ignored in presence of KEY3 on common layer')
        self.working.set(KEY3, VAL3)

        self.r.set(KEY1, NEW_VAL1)
        self.r.contract_idx = 2
        self.r.get(KEY2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.set(KEY3, NEW_VAL3)
        self.r.set(KEY4, NEW_VAL4)

        # Check state
        expected_state = "SET {k1} {v1};SET {k3} {v3};SET {k4} {v4}"\
                         .format(k1=KEY1, v1=NEW_VAL1, k2=KEY2, v2=VAL2, k3=KEY3, v3=NEW_VAL3, k4=KEY4, v4=NEW_VAL4)
        self.assertEqual(self.sbb_data[0]['getset'].get_state_rep(), expected_state)

    def test_unimplemented_method_raises_assert(self):
        with self.assertRaises(AssertionError):
            self.r.this_is_not_implemented('some_key')


if __name__ == "__main__":
    unittest.main()

