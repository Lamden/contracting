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

        self.r = RedisProxy(sbb_idx=sbb_idx, contract_idx=contract_idx, data=data)

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRContext(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def test_all_keys_and_values_for_basic_set_get(self):
        KEY1, VAL1 = 'k1', b'v1'
        KEY2, VAL2 = 'k2', b'v2'
        KEY3, VAL3 = 'k3', b'v3'
        NEW_VAL1 = b'v1_NEW'
        NEW_VAL3 = b'v3_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)
        self.working.set(KEY3, VAL3)

        self.r.set(KEY1, NEW_VAL1)
        self.r.contract_idx = 1
        self.r.get(KEY2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.set(KEY3, NEW_VAL3)  # To trigger a copy to sbb specific layer

        # Check the modified and original values
        getset = self.r.data['getset']
        k1_expected = {'og': VAL1, 'mod': NEW_VAL1, 'contracts': {0}}
        k2_expected = {'og': VAL2, 'mod': None, 'contracts': {1}}
        k3_expected = {'og': VAL3, 'mod': NEW_VAL3, 'contracts': {2}}
        self.assertEqual(getset[KEY1], k1_expected)
        self.assertEqual(getset[KEY2], k2_expected)
        self.assertEqual(getset[KEY3], k3_expected)

        # Check modifications list
        expected_mods = {0: {KEY1}, 2: {KEY3}}
        self.assertEqual(self.r.data['getset'].writes, expected_mods)

        # Check should_rerun (tinker with common first)
        cr_data = self.sbb_data[0]['getset']
        self.working.set(KEY1, b'A NEW VALUE HAS ARRIVED')
        self.working.set(KEY2, b'A NEW VALUE HAS ARRIVED AGAIN')
        self.assertTrue(0 in list(cr_data.get_rerun_list(reset_keys=False)))
        self.assertTrue(1 in list(cr_data.get_rerun_list(reset_keys=False)))
        self.assertFalse(2 in list(cr_data.get_rerun_list(reset_keys=False)))

    def test_merge_to_common(self):
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

        # Check merge_to_common
        cr_data = self.sbb_data[0]
        cr_data.merge_to_common()
        self.assertEqual(self.working.get(KEY1), NEW_VAL1)
        self.assertEqual(self.working.get(KEY2), None)  # None b/c we never SET KEY2
        self.assertEqual(self.working.get(KEY3), NEW_VAL3)
        self.assertEqual(self.working.get(KEY4), NEW_VAL4)

    def test_merge_to_master(self):
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

        # First merge_to_common
        cr_data = self.sbb_data[0]
        cr_data.merge_to_common()

        # Now check merge_to_master
        CRContext.merge_to_master(working_db=cr_data.working_db, master_db=cr_data.master_db)
        self.assertEqual(self.master.get(KEY1), NEW_VAL1)
        self.assertEqual(self.master.get(KEY2), VAL2)
        self.assertEqual(self.master.get(KEY3), NEW_VAL3)
        self.assertEqual(self.master.get(KEY4), NEW_VAL4)

    def test_state_rep(self):
        KEY1, VAL1 = 'k1', 'v1'
        KEY2, VAL2 = 'k2', 'v2'
        KEY3, VAL3 = 'k3', 'v3'
        KEY4, VAL4 = 'k4', 'v4'
        NEW_VAL1 = 'v1_NEW'
        NEW_VAL3 = 'v3_NEW'
        NEW_VAL4 = 'v4_NEW'

        # Seed keys on master
        self.master.set(KEY1, VAL1)
        self.master.set(KEY2, VAL2)
        self.master.set(KEY3, 'val 3 on master that should be ignored in presence of KEY3 on common layer')
        self.working.set(KEY3, VAL3)

        self.r.set(KEY1, NEW_VAL1)
        self.r.contract_idx = 1
        self.r.get(KEY2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.set(KEY3, NEW_VAL3)
        self.r.set(KEY4, NEW_VAL4)

        # Manually add the contracts/results being run. Store them so we can assert on them later
        expected_contracts = []
        expected_results = []
        for i in range(3):
            contract = 'contract_{}'.format(i)
            result = 'run_result_{}'.format(i)
            self.sbb_data[0].contracts.append(contract)
            self.sbb_data[0].run_results.append(result)
            expected_contracts.append(contract)
            expected_results.append(result)

        # Check entire subblock state
        expected_state = "SET {k1} {v1};SET {k3} {v3};SET {k4} {v4};"\
                         .format(k1=KEY1, v1=NEW_VAL1, k2=KEY2, v2=VAL2, k3=KEY3, v3=NEW_VAL3, k4=KEY4, v4=NEW_VAL4)
        self.assertEqual(self.sbb_data[0]['getset'].get_state_rep(), expected_state)

        # Check individual contract states
        cr_data = self.r.data
        state_0 = "SET {} {};".format(KEY1, NEW_VAL1)
        state_1 = ""
        state_2 = "SET {} {};SET {} {};".format(KEY3, NEW_VAL3, KEY4, NEW_VAL4)
        self.assertEqual(state_0, cr_data['getset'].get_state_for_idx(0))
        self.assertEqual(state_0, cr_data.get_state_for_idx(0))
        self.assertEqual(state_1, cr_data['getset'].get_state_for_idx(1))
        self.assertEqual(state_1, cr_data.get_state_for_idx(1))
        self.assertEqual(state_2, cr_data['getset'].get_state_for_idx(2))
        self.assertEqual(state_2, cr_data.get_state_for_idx(2))

        # Check sb rep...fake merged_to_common
        cr_data.merged_to_common = True
        expected_states = (state_0, state_1, state_2)
        expected_rep = []
        for i in range(3):
            expected_rep.append((expected_contracts[i], expected_results[i], expected_states[i]))

        self.assertEqual(expected_rep, cr_data.get_subblock_rep())

    def test_all_keys_and_values_for_basic_hset_hget(self):
        KEY1, KEY2 = 'KEY1', 'KEY2'
        FIELD1, VAL1 = 'k1', b'v1'
        FIELD2, VAL2 = 'k2', b'v2'
        FIELD3, VAL3 = 'k3', b'v3'
        NEW_VAL1 = b'v1_NEW'
        NEW_VAL3 = b'v3_NEW'

        # Seed keys on master
        self.master.hset(KEY1, FIELD1, VAL1)
        self.master.hset(KEY1, FIELD2, VAL2)
        self.master.hset(KEY2, FIELD3, b'val 3 on master that should be ignored in presence of KEY3 on common layer')
        self.working.hset(KEY2, FIELD3, VAL3)

        self.r.hset(KEY1, FIELD1, NEW_VAL1)
        self.r.contract_idx = 2
        self.r.hget(KEY1, FIELD2)  # To trigger a copy to sbb specific layer
        self.r.contract_idx = 2
        self.r.hset(KEY2, FIELD3, NEW_VAL3)  # To trigger a copy to sbb specific layer

        # Check the modified and original values
        hm = self.r.data['hm']
        k1_expected = {'og': VAL1, 'mod': NEW_VAL1}
        k2_expected = {'og': VAL2, 'mod': None}
        k3_expected = {'og': VAL3, 'mod': NEW_VAL3}
        self.assertEqual(hm[KEY1][FIELD1], k1_expected)
        self.assertEqual(hm[KEY1][FIELD2], k2_expected)
        self.assertEqual(hm[KEY2][FIELD3], k3_expected)

        print("Type of key k1: {}".format(self.master.type(KEY1)))

        # Check modifications list
        # TOFO fix and implement mod list for hmaps
        expected_mods = {KEY1: {FIELD1}, KEY2: {FIELD3}}
        # self.assertEqual(self.r.data['hm'].mods, expected_mods)

        # Check should_rerun (tinker with common first)
        # self.working.hset(FIELD1, b'A NEW VALUE HAS ARRIVED')
        # self.working.hset(FIELD2, b'A NEW VALUE HAS ARRIVED AGAIN')
        # self.assertTrue(self.sbb_data[0].should_rerun(0))
        # self.assertFalse(self.sbb_data[0].should_rerun(1))
        # self.assertFalse(self.sbb_data[0].should_rerun(2))

        # Check merge_to_common
        # cr_data = self.sbb_data[0]
        # cr_data.merge_to_common()
        # self.assertEqual(self.master.get(FIELD1), NEW_VAL1)
        # self.assertEqual(self.master.get(FIELD2), VAL2)
        # self.assertEqual(self.master.get(FIELD3), NEW_VAL3)

        # Check state
        # expected_state = "HNSET {k1} {f1};b'{v1};SET {k2};b'{v2}SET;{k3};b'{v3}"\
        #                  .format(k1=FIELD1, v1=NEW_VAL1, k2=KEY2, v2=VAL2, k3=KEY3, v3=VAL3)

    def test_unimplemented_method_raises_assert(self):
        with self.assertRaises(AssertionError):
            self.r.this_is_not_implemented('some_key')


if __name__ == "__main__":
    unittest.main()

