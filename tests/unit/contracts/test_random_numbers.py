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


class TestRandomNumbers(TestCase):
    CONTRACTS_TO_STORE = {'random_nums': 'random_nums_test.sen.py',
                          'importing_randoms': 'importing_randoms.sen.py',
                          'currency': 'currency.sen.py'}

    def setUp(self):
        context = {
            'sbb_idx': None,
            'contract_idx': None,
            'data': None,
            'last_block_hash': b'abc'
        }
        BookKeeper.set_cr_info(**context)

        # overwrite_logger_level(0)
        with SenecaInterface(False, bypass_currency=True) as interface:
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
        with SenecaInterface(False, bypass_currency=True) as interface:
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

        self.assertEqual(f['output'], f2['output'])

    def test_random_num_imports(self):
        with SenecaInterface(False, bypass_currency=True) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.importing_randoms.yo',
                sender=GENESIS_AUTHOR,
                stamps=None,
            )

    def test_random_num_one_vs_two(self):
        with SenecaInterface(False, bypass_currency=True) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.random_nums.random_number',
                sender=GENESIS_AUTHOR,
                stamps=None,
                k=1000
            )

            f2 = interface.execute_function(
                module_path='seneca.contracts.random_nums.random_number_2',
                sender=GENESIS_AUTHOR,
                stamps=None,
                k=1000
            )
        self.assertEqual(f['output'], 790)
        self.assertEqual(f2['output'], 220)

    def test_random_getrandbits(self):
        with SenecaInterface(False, bypass_currency=True) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.random_nums.random_bits',
                sender=GENESIS_AUTHOR,
                stamps=None,
                k=20
            )

        self.assertEqual(f['output'], 386311)

    def test_random_range_int(self):
        with SenecaInterface(False, bypass_currency=True) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.random_nums.int_in_range',
                sender=GENESIS_AUTHOR,
                stamps=None,
                a=100,
                b=50000
            )

            f2 = interface.execute_function(
                module_path='seneca.contracts.random_nums.int_in_range',
                sender=GENESIS_AUTHOR,
                stamps=None,
                a=100,
                b=50000
            )

        self.assertEqual(f['output'], 17977)
        self.assertEqual(f2['output'], 22879)

    def test_random_choice(self):
        with SenecaInterface(False, bypass_currency=True) as interface:
            f = interface.execute_function(
                module_path='seneca.contracts.random_nums.pick_cities',
                sender=GENESIS_AUTHOR,
                stamps=None,
                k=2
            )

        self.assertEqual(f['output'], ['New York', 'Chicago'])
