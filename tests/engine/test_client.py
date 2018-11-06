from unittest import TestCase
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface


XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('stu', 3)
"""

MINT_CODE_STR = """ \

from seneca.contracts.currency import mint
mint('davis', 100000)
mint('stu', 69)
"""

class MockContract:
    def __init__(self, sender: str, code_str: str):
        self.sender, self.code_str = sender, code_str


def create_currency_tx(sender: str, receiver: str, amount: int):
    pass


class TestSenecaClient(TestCase):
    CONTRACTS_TO_STORE = {'runtime_test': 'runtime_test.sen.py', 'sample': 'sample.sen.py',
                          'currency': 'kv_currency.sen.py'}

    @classmethod
    def setUpClass(cls):
        with SenecaInterface()

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

    def test_setup_dbs(self):
        client = SenecaClient(sbb_idx=0, num_sbb=4)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is not None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES - 1)  # -1 for the current active db

    def test_run_

