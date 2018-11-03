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

    def test_get_from_master(self):
        KEY = 'im_a_key'
        VALUE = 'value_on_master'
        cr_get = CRGet(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        self.master.set(KEY, VALUE)

        actual = cr_get(KEY).decode()

        self.assertEqual(actual, VALUE)

    def test_get_from_common(self):
        KEY = 'im_a_key'
        VALUE_M = 'value_on_master'
        VALUE_C = 'value_on_common'
        cr_get = CRGet(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        self.master.set(KEY, VALUE_M)
        self.working.set(cr_get._common_key(KEY), VALUE_C)

        actual = cr_get(KEY).decode()

        self.assertEqual(actual, VALUE_C)

    def test_get_from_sbb_specific(self):
        KEY = 'im_a_key'
        VALUE_M = 'value_on_master'
        VALUE_C = 'value_on_common'
        VALUE_SBB = 'value_on_sbb'
        cr_get = CRGet(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        self.master.set(KEY, VALUE_M)
        self.working.set(cr_get._common_key(KEY), VALUE_C)
        self.working.set(cr_get._sbb_modified_key(KEY), VALUE_SBB)

        actual = cr_get(KEY).decode()

        self.assertEqual(actual, VALUE_SBB)

    def test_get_copies_original_from_master(self):
        KEY = 'im_a_key'
        VALUE_M = 'value_on_master'
        cr_get = CRGet(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        self.master.set(KEY, VALUE_M)

        cr_get(KEY).decode()

        og_sbb_key = cr_get._sbb_original_key(KEY)
        self.assertTrue(self.working.exists(og_sbb_key))

        actual = self.working.get(og_sbb_key).decode()
        self.assertEqual(VALUE_M, actual)

    def test_get_copies_original_from_common(self):
        KEY = 'im_a_key'
        VALUE_M = 'value_on_master'
        VALUE_C = 'value_on_common'
        cr_get = CRGet(working_db=self.working, master_db=self.master, sbb_idx=0, contract_idx=0)
        self.master.set(KEY, VALUE_M)
        self.working.set(cr_get._common_key(KEY), VALUE_C)

        cr_get(KEY).decode()

        og_sbb_key = cr_get._sbb_original_key(KEY)
        self.assertTrue(self.working.exists(og_sbb_key))

        actual = self.working.get(og_sbb_key).decode()
        self.assertEqual(VALUE_C, actual)


if __name__ == "__main__":
    unittest.main()

