from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.book_keeper import BookKeeper
from decimal import *

GENESIS_AUTHOR = 'davis'
STAMP_AMOUNT = None
MINT_WALLETS = {
    'davis': 10000,
    'stu': 69,
    'birb': 8000,
    'ghu': 9000,
    'tj': 8000,
    'ethan': 8000
}


class TestSenecaClient(TestCase):
    CONTRACTS_TO_STORE = {'random_nums': 'random_nums_test.sen.py'}

    def setUp(self):
        context = {
            'sbb_idx': None,
            'contract_idx': None,
            'data': None,
            'last_block_hash': b'abc'
        }
        BookKeeper.set_info(**context)

        # overwrite_logger_level(0)
        with SenecaInterface(False) as interface:
            interface.r.flushall()
            # Store all smart contracts in CONTRACTS_TO_STORE
            import seneca
            test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

            for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
                with open(test_contracts_path + file_name) as f:
                    code_str = f.read()
                    interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)

            rt = {
                'author': GENESIS_AUTHOR,
                'sender': GENESIS_AUTHOR,
                'contract': 'minter'
            }

    def test_shuffle_cards(self):
        with SenecaInterface(False) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.random_nums.shuffle_cards',
                sender=GENESIS_AUTHOR,
                stamps=None,
            )

            f2 = interface.execute_function(
                module_path='seneca.contracts.random_nums.shuffle_cards',
                sender=GENESIS_AUTHOR,
                stamps=None,
            )
        print(f, f2)
