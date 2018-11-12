from unittest import TestCase
from seneca.engine.book_keeper import BookKeeper
from unittest.mock import patch
from multiprocessing import Process
import threading, unittest
from seneca.engine.conflict_resolution import CRContext


class TestBookKeeper(TestCase):

    def _build_info_dict(self, sbb_idx=0, contract_idx=0, master_db='', working_db=''):
        master_db = master_db or 'some placeholder that irl would be a redis client cursor'
        working_db = working_db or 'another placeholder that irl would be a redis client cursor'
        data = CRContext(working_db=working_db, master_db=master_db, sbb_idx=sbb_idx, finalize=False)

        info = {'sbb_idx': sbb_idx, 'contract_idx': contract_idx, 'data': data}
        return info

    def test_set_and_get_info(self):
        expected_info = self._build_info_dict(sbb_idx=8, contract_idx=10)

        BookKeeper.set_info(**expected_info)
        actual_info = BookKeeper.get_info()

        self.assertEqual(actual_info, expected_info)

    def test_set_and_get_multiproc(self):
        # TODO -- implement ... spin up multiple theads/procs and ensure each has a different ID. Will have to write
        # to some shared Queue object so that the assertions can be checked on the main process (the one running this test)
        pass
        # with patch('os.getpid') as pid_func:
        #     with patch('threading.get_ident') as id_func:
        #         mock_pid = 100
        #         mock_thread = 90
        #         pid_func.return_value = mock_pid
        #         id_func.return_value = mock_thread
        #
        #         print("Got key: {}".format(BookKeeper._get_key()))


if __name__ == '__main__':
    unittest.main()
