from unittest import TestCase
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.util import make_n_tup
import redis, unittest, sys

CODE_STR = """ \

from seneca.contracts.sample import do_that_thing
do_that_thing()
"""


class TestInterpreter(TestCase):

    CONTRACTS_TO_STORE = {'runtime_test': 'runtime_test.sen.py', 'sample': 'sample.sen.py'}

    @classmethod
    def setUpClass(cls):
        cls.old_meta_path = sys.meta_path
        sys.meta_path = [SenecaFinder(), RedisFinder()]
        SenecaInterpreter.r.flushdb()

        # Store all smart contracts in CONTRACTS_TO_STORE
        import seneca
        test_contracts_path = seneca.__path__[0] + '/test_contracts/'

        for contract_name, file_name in cls.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code = f.read()
                SenecaInterpreter.set_code(fullname=contract_name, code_str=code, keep_original=True)

    @classmethod
    def tearDownClass(cls):
        SenecaInterpreter.r.flushdb()
        sys.meta_path = cls.old_meta_path

    def test_execute_with_bookkeeping_info(self):
        bk_info = {'sbb_idx': 2, 'contract_idx': 12}
        rt_info = {'rt': make_n_tup({'sender': 'davis', 'author': 'davis'})}
        all_info = {**bk_info, **rt_info}

        tree = SenecaInterpreter.parse_ast(CODE_STR)
        code_obj = compile(tree, filename='__main__', mode="exec")
        print("ALL INFO: {}".format(all_info))
        SenecaInterpreter.execute(code_obj, scope=all_info)


