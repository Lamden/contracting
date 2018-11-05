from seneca.engine.conflict_resolution import *
from seneca.engine.cr_commands import *
import redis
from unittest import TestCase
import unittest


class TestCRData(TestCase):

    def setUp(self):
        self.master = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.working = redis.StrictRedis(host='localhost', port=6379, db=1)

    def tearDown(self):
        self.master.flushdb()
        self.working.flushdb()

    def _new_cr_data(self, sbb_idx=0, finalize=False):
        return CRDataContainer(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, finalize=finalize)

    def _new_cmd(self, sbb_idx=0, contract_idx=0, cr_data=None, finalize=False):
        return CRCmdBase(working_db=self.working, master_db=self.master, sbb_idx=sbb_idx, contract_idx=contract_idx,
                         data=cr_data or self._new_cr_data(sbb_idx=sbb_idx, finalize=finalize))




if __name__ == "__main__":
    unittest.main()
