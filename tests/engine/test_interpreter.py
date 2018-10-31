from unittest import TestCase
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.util import make_n_tup
import redis, unittest, sys

DO_THING_CODE_STR = """ \

from seneca.contracts.sample import do_that_thing
print(do_that_thing())
"""

XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('stu', 3)
"""

MINT_CODE_STR = """ \

from seneca.contracts.currency import mint
mint('davis', 100000)
mint('stu', 69)
"""


class TestInterpreter(TestCase):

    CONTRACTS_TO_STORE = {'runtime_test': 'runtime_test.sen.py', 'sample': 'sample.sen.py',
                          'currency': 'kv_currency.sen.py'}

    @classmethod
    def setUpClass(cls):
        SenecaInterpreter.setup(concurrent_mode=False)
        SenecaInterpreter.r.flushdb()

        # Store all smart contracts in CONTRACTS_TO_STORE
        import seneca
        test_contracts_path = seneca.__path__[0] + '/test_contracts/'

        for contract_name, file_name in cls.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code = f.read()
                SenecaInterpreter.set_code(fullname=contract_name, code_str=code, keep_original=True)

        cls._mint()

    @classmethod
    def _exec_code(cls, code_str: str, sender='davis', sbb_idx=0, contract_idx=0, author='davis', master_db_idx=0,
                   working_db_idx=1):
        master_db = redis.StrictRedis(host='localhost', port=6379, db=master_db_idx)
        working_db = redis.StrictRedis(host='localhost', port=6379, db=working_db_idx)
        SenecaInterpreter.execute_contract(code_str=code_str, sender=sender, sbb_idx=sbb_idx, contract_idx=contract_idx,
                                           master_db=master_db, working_db=working_db, author=author)

    @classmethod
    def _mint(cls):
        # SenecaInterpreter.execute_contract(code_str=MINT_CODE_STR, sender='davis', sbb_idx=0, contract_idx=0,
        #                                    author='davis')
        cls._exec_code(MINT_CODE_STR)

    @classmethod
    def tearDownClass(cls):
        SenecaInterpreter.r.flushdb()
        SenecaInterpreter.teardown()

    def test_transfer_with_bookkeeping(self):
        # SenecaInterpreter.execute_contract(code_str=XFER_CODE_STR, sender='davis', sbb_idx=2, contract_idx=4)
        self._exec_code(XFER_CODE_STR)


if __name__ == '__main__':
    unittest.main()
