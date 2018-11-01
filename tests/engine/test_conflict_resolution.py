from seneca.libs.datatypes import *   # This code most be interpretted for the metaclass stuff to get run
from seneca.engine.conflict_resolution import *
import redis
from unittest import TestCase


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

    def test_basic_read_from_master(self):
        KEY = 'ass'
        VALUE = b'fast'

        self.master.set(KEY, VALUE)
        val = self.rp.get(KEY)

        self.assertEqual(VALUE, val)

    def test_basic_read_finalize(self):
        self._set_rp(finalize=True)

        KEY = 'ass'
        VALUE = b'fast'
        # common_key = self.rp.ds._common_prefix_for_key(KEY)

        # self.working.set(common_key, VALUE)
        # self.master.set(KEY, VALUE)
        val = self.rp.get(KEY)

        self.assertEqual(VALUE, val)

    def test_complex_read_from_master(self):
        KEY = 'ass'
        VAL1 = b'im the min'
        VAL2 = b'im the max'

        self.master.zadd(KEY, 1, VAL1)
        self.master.zadd(KEY, 100, VAL2)

        min_ = self.rp.zrangebyscore(KEY, min='-inf', max='+inf', start=0, num=1)
        max_ = self.rp.zrevrangebyscore(KEY, min='-inf', max='+inf', start=0, num=1)

        self.assertEqual(min_[0], VAL1)
        self.assertEqual(max_[0], VAL2)

    def test_complex_read_finalize(self):
        self._set_rp(finalize=True)

        KEY = 'ass'
        VAL1 = b'im the min'
        VAL2 = b'im the max'
        common_key = self.rp.ds._common_prefix_for_key(KEY)

        self.working.zadd(common_key, 1, VAL1)
        self.working.zadd(common_key, 100, VAL2)

        min_ = self.rp.zrangebyscore(KEY, min='-inf', max='+inf', start=0, num=1)
        max_ = self.rp.zrevrangebyscore(KEY, min='-inf', max='+inf', start=0, num=1)

        self.assertEqual(min_[0], VAL1)
        self.assertEqual(max_[0], VAL2)

    def test_basic_write_non_finalize(self):
        KEY = 'ass'
        VAL = b'fast'
        sbb_key = self.rp.ds._sbb_prefix_for_key(KEY)

        self.rp.set(KEY, VAL)
        result = self.working.get(sbb_key)

        self.assertEqual(VAL, result)

    def test_complex_write_non_finalize(self):
        KEY = 'ass'
        sbb_key = self.rp.ds._sbb_prefix_for_key(KEY)
        VAL1 = b'im the min'
        VAL2 = b'im the max'

        self.rp.zadd(KEY, 1, VAL1)
        self.rp.zadd(KEY, 100, VAL2)

        min_ = self.working.zrangebyscore(sbb_key, min='-inf', max='+inf', start=0, num=1)
        max_ = self.working.zrevrangebyscore(sbb_key, min='-inf', max='+inf', start=0, num=1)

        self.assertEqual(min_[0], VAL1)
        self.assertEqual(max_[0], VAL2)

    def test_write_adds_mods(self):
        pass



