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
        return CRDataContainer(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

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
        cr_get.data['getset'][KEY] = {'og': VALUE_SBB, 'mod': None}

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
        cr_get.data['getset'][KEY] = {'og': VALUE_SBB_OG, 'mod': VALUE_SBB_MOD}

        actual = cr_get(KEY)

        self.assertEqual(actual, VALUE_SBB_MOD)

    def test_get_copies_original_from_master(self):
        KEY = 'im_a_key'
        VALUE_M = b'value_on_master'
        cr_get = self._new_get()
        self.master.set(KEY, VALUE_M)

        cr_get(KEY)  # calling get should trigger the key to be copied to the SBB specific layer

        self.assertTrue(cr_get._sbb_original_exists(KEY))
        self.assertEqual(cr_get.data['getset'][KEY], {'og': VALUE_M, 'mod': None})

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

        expected = {'og': VALUE, 'mod': NEW_VALUE}
        self.assertEqual(expected, cr_set.data['getset'][KEY])

    def test_adds_key_that_does_not_yet_exist(self):
        KEY = 'im_a_key'
        VALUE = b'g00d_val'
        cr_set = self._new_set()

        cr_set(KEY, VALUE)

        expected = {'og': None, 'mod': VALUE}
        self.assertEqual(expected, cr_set.data['getset'][KEY])


if __name__ == "__main__":
    unittest.main()

