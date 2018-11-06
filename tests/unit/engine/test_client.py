from unittest import TestCase
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface


GENESIS_AUTHOR = 'davis'


XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('{receiver}', {amount})
"""


MINT_CODE_STR = """ \

from seneca.contracts.currency import mint
mint('davis', 100000)
mint('stu', 69)
"""


class MockContract:
    def __init__(self, sender: str, code: str, contract_name: str):
        self.sender, self.code, self.contract_name = sender, code, contract_name


def create_currency_tx(sender: str, receiver: str, amount: int, contract_name: str='currency'):
    code = XFER_CODE_STR.format(receiver=receiver, amount=amount)
    contract = MockContract(sender=sender, code=code, contract_name=contract_name)
    return contract


class TestSenecaClient(TestCase):
    CONTRACTS_TO_STORE = {'currency': 'kv_currency.sen.py'}

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
        self.assertTrue(client.active_db is None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES)

    def test_run_tx_increments_contract_idx(self):
        client = SenecaClient(sbb_idx=0, num_sbb=4)
        client.start_sub_block('A' * 64)

        self.assertEqual(client.active_db.next_contract_idx, 0)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)

        client.run_contract(c1)
        self.assertEqual(client.active_db.next_contract_idx, 1)

        client.run_contract(c2)
        self.assertEqual(client.active_db.next_contract_idx, 2)

    def test_end_subblock(self):
        client = SenecaClient(sbb_idx=0, num_sbb=4)
        client.start_sub_block('A' * 64)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        client.run_contract(c1)
        client.run_contract(c2)




