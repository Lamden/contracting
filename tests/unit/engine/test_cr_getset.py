from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest


class TestCRGetSet(TestCase):

    def setUp(self):
        self.master = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.working = redis.StrictRedis(host='localhost', port=6379, db=1)
        self.sbb_data = {}

    def tearDown(self):
        self.master.flushdb()
        self.working.flushdb()

    def _new_getset(self, should_set=True, sbb_idx=0, contract_idx=0, finalize=False):
        if contract_idx in self.sbb_data:
            data = self.sbb_data[contract_idx]
        else:
            data = self._new_cr_data(sbb_idx=sbb_idx, finalize=finalize)
            self.sbb_data[contract_idx] = data

        if should_set:
            return CRCmdSet(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                            data=data)
        else:
            return CRCmdGet(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                            data=data)

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRContext(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def _new_get(self, sbb_idx=0, contract_idx=0, finalize=False):
        return self._new_getset(should_set=False, sbb_idx=0, contract_idx=contract_idx, finalize=finalize)

    def _new_set(self, sbb_idx=0, contract_idx=0, finalize=False):
        return self._new_getset(should_set=True, sbb_idx=0, contract_idx=contract_idx, finalize=finalize)

    def test_get_from_master(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE)

        actual = cr_get(KEY)

        self.assertEqual(actual, VALUE)

    def test_get_from_common(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)
        self.working.set(KEY, VALUE_C)

        actual = cr_get(KEY)

        self.assertEqual(actual, VALUE_C)

    def test_get_from_sbb_specific_original(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        VALUE_SBB = b'value_on_sbb'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)
        self.working.set(KEY, VALUE_C)
        cr_get.data['getset'][KEY] = {'og': VALUE_SBB, 'mod': None, 'contracts': {0}}

        actual = cr_get(KEY)

        self.assertEqual(actual, VALUE_SBB)

    def test_get_from_sbb_specific_modified(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        VALUE_SBB_OG = b'value_on_sbb_og'
        VALUE_SBB_MOD = b'value_on_sbb_mod'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)
        self.working.set(KEY, VALUE_C)
        cr_get.data['getset'][KEY] = {'og': VALUE_SBB_OG, 'mod': VALUE_SBB_MOD, 'contracts': {0}}

        actual = cr_get(KEY)

        self.assertEqual(actual, VALUE_SBB_MOD)

    def test_get_copies_original_from_master(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)

        cr_get(KEY)  # calling get should trigger the key to be copied to the SBB specific layer

        self.assertTrue(cr_get._sbb_original_exists(KEY))
        self.assertEqual(cr_get.data['getset'][KEY], {'og': VALUE_M, 'mod': None, 'contracts': {0}})

    def test_get_copies_original_from_common(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)
        self.working.set(KEY, VALUE_C)

        cr_get(KEY)  # calling get should trigger the key to be copied to the SBB specific layer

        self.assertTrue(cr_get._sbb_original_exists(KEY))

        actual = cr_get(KEY)
        self.assertEqual(VALUE_C, actual)

    def test_basic_set(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set(KEY, NEW_VALUE)

        expected = {'og': VALUE, 'mod': NEW_VALUE, 'contracts': {0}}
        self.assertEqual(expected, cr_set.data['getset'][KEY])

    def test_basic_set_adds_to_redo_log(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set(KEY, NEW_VALUE)

        self.assertEqual(cr_set.data['getset'].redo_log[0][KEY], VALUE)

    def test_basic_set_new_key_adds_to_redo_log(self):
        KEY = 'im_a_key'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()

        cr_set(KEY, NEW_VALUE)

        self.assertEqual(cr_set.data['getset'].redo_log[0][KEY], None)

    def test_basic_set_adds_to_writes(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set(KEY, NEW_VALUE)

        writes = cr_set.data['getset'].writes
        self.assertTrue(KEY in writes[0])

    def test_basic_set_adds_to_key_contract_mods(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set(KEY, NEW_VALUE)

        contracts_mod = cr_set.data['getset'][KEY]['contracts']
        self.assertTrue(cr_set.contract_idx in contracts_mod)

    def test_basic_get_adds_to_reads(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE)

        actual = cr_get(KEY)
        self.assertEqual(actual, VALUE)

        reads = cr_get.data['getset'].reads
        self.assertTrue(KEY in reads[0])

    def test_basic_set_and_rollback(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        cr_set = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set(KEY, NEW_VALUE)

        cr_set.data['getset'].rollback_contract(0)
        expected = {'og': VALUE, 'mod': VALUE, 'contracts': set()}
        self.assertEqual(expected, cr_set.data['getset'][KEY])

    def test_basic_set_and_rollback_two_contracts(self):
        KEY = 'im_a_key'
        VALUE = b'value_on_master'
        NEW_VALUE = b'new_value'
        NEWER_VALUE = b'newer_value'
        cr_set1 = self._new_set()
        self.master.set(KEY, VALUE)

        cr_set1(KEY, NEW_VALUE)

        cr_set2 = self._new_set(contract_idx=1)
        cr_set2(KEY, NEWER_VALUE)

        cr_set2.data['getset'].rollback_contract(1)
        expected = {'og': VALUE, 'mod': NEW_VALUE, 'contracts': {0}}
        self.assertEqual(expected, cr_set1.data['getset'][KEY])

    def test_basic_setget_and_reset_contract_data(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        cr_get = self._new_get()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_get(KEY2)
        cr_set(KEY1, NEW_VALUE1)

        cr_get.data['getset'].reset_contract_data(0)
        self.assertEqual(len(cr_set.data['getset'].writes[0]), 0)
        self.assertEqual(len(cr_set.data['getset'].reads[0]), 0)

    def test_adds_key_that_does_not_yet_exist(self):
        KEY = 'im_a_key'
        VALUE = b'g00d_val'
        cr_set = self._new_set()

        cr_set(KEY, VALUE)

        expected = {'og': None, 'mod': VALUE, 'contracts': {0}}
        self.assertEqual(expected, cr_set.data['getset'][KEY])

    def test_should_rerun_no_changes(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        cr_get = self._new_get()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_get(KEY2)
        cr_set(KEY1, NEW_VALUE1)

        cr_data = cr_set.data['getset']
        self.assertFalse(0 in list(cr_data.get_rerun_list(reset_keys=False)))

    def test_should_rerun_change_common_only_write(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to common on the written key
        self.working.set(KEY1, b'new_common1')

        cr_data = cr_set.data['getset']
        self.assertTrue(0 in list(cr_data.get_rerun_list(reset_keys=False)))


    def test_should_rerun_change_common_only_read(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        cr_get = self._new_get()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_get(KEY1)

        # Make some changes to common on the written key
        self.working.set(KEY1, b'new_common1')

        cr_data = cr_get.data['getset']
        self.assertTrue(0 in list(cr_data.get_rerun_list(reset_keys=False)))

    def test_should_rerun_change_master_only_read(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        cr_get = self._new_get()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_get(KEY1)

        # Make some changes to common on the written key
        self.master.set(KEY1, b'new_common1')

        cr_data = cr_get.data['getset']
        self.assertTrue(0 in list(cr_data.get_rerun_list(reset_keys=False)))

    def test_should_rerun_change_master_only_write(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to common on the written key
        self.master.set(KEY1, b'new_common1')

        cr_data = cr_set.data['getset']
        self.assertTrue(0 in list(cr_data.get_rerun_list(reset_keys=False)))

    def test_get_modified_keys_from_common(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to common on the written key
        self.working.set(KEY1, b'new_common1')

        cr_data = cr_set.data['getset']
        actual_mods = cr_data.get_modified_keys()
        expected_mods = {KEY1}
        self.assertEqual(expected_mods, actual_mods)

    def test_get_modified_keys_from_master(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to master on the written key
        self.master.set(KEY1, b'new_common1')

        cr_data = cr_set.data['getset']
        actual_mods = cr_data.get_modified_keys()
        expected_mods = {KEY1}
        self.assertEqual(expected_mods, actual_mods)

    def test_reset_key_from_common(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        COMMON_VALUE1 = b'new_common1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to common on the written key
        self.working.set(KEY1, COMMON_VALUE1)

        cr_data = cr_set.data['getset']
        cr_data.reset_key(KEY1)

        self.assertEqual(cr_data[KEY1]['og'], COMMON_VALUE1)
        self.assertEqual(cr_data[KEY1]['mod'], None)

    def test_reset_key_from_master(self):
        KEY1 = 'im_a_key1'
        KEY2 = 'im_a_key2'
        VALUE1 = b'value_on_master1'
        VALUE2 = b'value_on_master2'
        NEW_VALUE1 = b'new_value1'
        COMMON_VALUE1 = b'new_common1'
        MASTER_VALUE1 = b'new_master1'
        cr_set = self._new_set()
        self.master.set(KEY1, VALUE1)
        self.master.set(KEY2, VALUE2)

        cr_set(KEY1, NEW_VALUE1)

        # Make some changes to master on the written key
        self.master.set(KEY1, MASTER_VALUE1)

        cr_data = cr_set.data['getset']
        cr_data.reset_key(KEY1)

        self.assertEqual(cr_data[KEY1]['og'], MASTER_VALUE1)
        self.assertEqual(cr_data[KEY1]['mod'], None)

    def test_get_modified_keys_recursive(self):
        k = ['k{}'.format(i+1) for i in range(5)]
        v = ['v{}'.format(i+1) for i in range(5)]

        cr_set = self._new_set()
        cr_data = cr_set.data['getset']

        for i in range(len(k)):
            cr_data[k[i]] = {'og': v[i], 'mod': v[i] + '_MOD', 'contracts': set()}

        cr_data[k[0]]['contracts'] = {0, 2}
        cr_data[k[1]]['contracts'] = {0, 3}
        cr_data[k[2]]['contracts'] = {1}
        cr_data[k[3]]['contracts'] = {2}
        cr_data[k[4]]['contracts'] = {3}

        cr_data.writes[0] = {k[0], k[1]}
        cr_data.reads[0] = {k[1]}

        cr_data.writes[1] = {k[2]}
        cr_data.reads[1] = {k[2]}

        cr_data.writes[2] = {k[0], k[3]}
        cr_data.reads[2] = {k[0]}

        cr_data.writes[3] = {k[1], k[4]}
        cr_data.reads[3] = {k[1]}

        self.master.set(k[3], 'SOME NEW VALUE FOR k[3]')

        expected_mods = {k[3], k[0], k[1], k[4]}
        actual_mods = cr_data.get_modified_keys_recursive()
        self.assertEqual(expected_mods, actual_mods)


if __name__ == "__main__":
    unittest.main()
