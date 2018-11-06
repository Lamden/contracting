from unittest import TestCase
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface


GENESIS_AUTHOR = 'davis'


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
        with SenecaInterface() as interface:
            interface.r.flushall()

            # Store all smart contracts in CONTRACTS_TO_STORE
            import seneca
            test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

            for contract_name, file_name in cls.CONTRACTS_TO_STORE.items():
                with open(test_contracts_path + file_name) as f:
                    code_str = f.read()
                    interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str, keep_original=True)

            rt = make_n_tup({
                'author': GENESIS_AUTHOR,
                'sender': GENESIS_AUTHOR,
            })
            interface.execute_code_str(MINT_CODE_STR, scope={'rt': rt})

    def test_setup_dbs(self):
        client = SenecaClient(sbb_idx=0, num_sbb=4)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is not None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES - 1)  # -1 for the current active db

    def test_run_currency_tx(self):
        pass

    # def test_run_

