from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest


class TestCRHMap(TestCase):

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
            return CRCmdHSet(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                             data=data)
        else:
            return CRCmdHGet(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                             data=data)

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRContext(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def _new_get(self, sbb_idx=0, contract_idx=0, finalize=False):
        return self._new_getset(should_set=False, sbb_idx=0, contract_idx=contract_idx, finalize=finalize)

    def _new_set(self, sbb_idx=0, contract_idx=0, finalize=False):
        return self._new_getset(should_set=True, sbb_idx=0, contract_idx=contract_idx, finalize=finalize)

    def test_get_from_master(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE = b'value_on_master'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE)

        actual = cr_get(KEY, FIELD)

        self.assertEqual(actual, VALUE)
        self.assertEqual({'og': VALUE, 'mod': None}, cr_get.data['hm'][KEY][FIELD])

    def test_get_from_common(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE_M)
        self.working.hset(KEY, FIELD, VALUE_C)

        actual = cr_get(KEY, FIELD)

        self.assertEqual(actual, VALUE_C)
        self.assertEqual({'og': VALUE_C, 'mod': None}, cr_get.data['hm'][KEY][FIELD])

    def test_get_from_sbb_specific_original(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        VALUE_SBB = b'value_on_sbb'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE_M)
        self.working.hset(KEY, FIELD, VALUE_C)
        cr_get.data['hm'][KEY][FIELD] = {'og': VALUE_SBB, 'mod': None}

        actual = cr_get(KEY, FIELD)

        self.assertEqual(actual, VALUE_SBB)

    def test_get_from_sbb_specific_modified(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        VALUE_SBB_OG = b'value_on_sbb_og'
        VALUE_SBB_MOD = b'value_on_sbb_mod'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE_M)
        self.working.hset(KEY, FIELD, VALUE_C)
        cr_get.data['hm'][KEY][FIELD] = {'og': VALUE_SBB_OG, 'mod': VALUE_SBB_MOD}

        actual = cr_get(KEY, FIELD)

        self.assertEqual(actual, VALUE_SBB_MOD)

    def test_get_copies_original_from_master(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE_M = b'value_on_master'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE_M)

        cr_get(KEY, FIELD)  # calling get should trigger the key to be copied to the SBB specific layer

        self.assertTrue(cr_get._sbb_original_exists(KEY, FIELD))
        self.assertEqual(cr_get.data['hm'][KEY][FIELD], {'og': VALUE_M, 'mod': None})

    def test_get_copies_original_from_common(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE_M = b'value_on_master'
        VALUE_C = b'value_on_common'
        cr_get = self._new_get()
        self.master.hset(KEY, FIELD, VALUE_M)
        self.working.hset(KEY, FIELD, VALUE_C)

        cr_get(KEY, FIELD)  # calling get should trigger the key to be copied to the SBB specific layer

        self.assertTrue(cr_get._sbb_original_exists(KEY, FIELD))

        actual = cr_get(KEY, FIELD)
        self.assertEqual(VALUE_C, actual)

    # TODO fix this test once we implement write log for hash maps
    # def test_basic_set(self):
    #     KEY = 'im_a_key'
    #     FIELD = 'im_a_field'
    #     VALUE = b'value_on_master'
    #     NEW_VALUE = b'new_value'
    #     cr_set = self._new_set()
    #     cr_get = self._new_get()
    #     self.master.hset(KEY, FIELD, VALUE)
    #     cr_set(KEY, FIELD, NEW_VALUE)
    #
    #     expected = {'og': VALUE, 'mod': NEW_VALUE}
    #     expected_mod = cr_set._get_key_field_name(KEY, FIELD)
    #     actual_mods = cr_set.data['hm'].mods
    #     self.assertEqual(expected, cr_set.data['hm'][KEY][FIELD])
    #     self.assertEqual(expected['mod'], cr_get(KEY, FIELD))
    #
    #     self.assertEqual(len(actual_mods), 1)
    #     self.assertEqual(actual_mods[0], {expected_mod})

    def test_adds_key_that_does_not_yet_exist(self):
        KEY = 'im_a_key'
        FIELD = 'im_a_field'
        VALUE = b'g00d_val'
        cr_set = self._new_set()

        cr_set(KEY, FIELD, VALUE)

        expected = {'og': None, 'mod': VALUE}
        self.assertEqual(expected, cr_set.data['hm'][KEY][FIELD])


if __name__ == "__main__":
    unittest.main()

