from unittest import TestCase
from seneca.engine.interpreter import SenecaInterpreter
import redis, unittest, sys

DO_THING_CODE_STR = """ \

from seneca.contracts.sample import do_that_thing
print(do_that_thing())
"""

XFER_CODE_STR = """ \

from seneca.contracts.currency import mint, transfer
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
        test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

        for contract_name, file_name in cls.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                assert not SenecaInterpreter.r.hexists('contracts', contract_name), 'Contract "{}" already exists!'.format(contract_name)
                tree, prevalidated = SenecaInterpreter.parse_ast(code_str)
                prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
                SenecaInterpreter.execute(prevalidated_obj)
                code_obj = compile(tree, filename='__main__', mode="exec")
                SenecaInterpreter.set_code(fullname=contract_name, author='davis', code_obj=code_obj, code_str=code_str, keep_original=True)

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
        cls._exec_code(MINT_CODE_STR)

    @classmethod
    def tearDownClass(cls):
        SenecaInterpreter.r.flushdb()
        SenecaInterpreter.teardown()

    def test_transfer_with_bookkeeping(self):
        self._exec_code(XFER_CODE_STR)


if __name__ == '__main__':
    unittest.main()
