from tests.utils import TestExecutor
import seneca, os
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
test_contracts_path = os.path.dirname(seneca.__path__[0]) + '/test_contracts/'


class TestFloatArithmetics(TestExecutor):
    CONTRACTS_TO_STORE = {'decimal_test': 'decimal_test.sen.py'}

    def setUp(self):
        self.flush()
        for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                self.ex.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)

    def test_store_float(self):
        self.ex.execute_function(
            'decimal_test',
            'store_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty',
                'f': Decimal('0.01')
            }
        )

        f = self.ex.execute_function(
            'decimal_test',
            'read_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty'
            }
        )

        self.assertEqual(f['output'], Decimal('0.01'))

    def test_add_floats(self):
        self.ex.execute_function(
            'decimal_test',
            'store_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty',
                'f': Decimal('1.1')
            }
        )

        self.ex.execute_function(
            'decimal_test',
            'store_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty2',
                'f': Decimal('2.2')
            }
        )

        f = self.ex.execute_function(
            'decimal_test',
            'add_floats',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's1': 'floaty',
                's2': 'floaty2'
            }
        )

        self.assertEqual(f['output'], Decimal('3.3'))

    def test_divide_float(self):
        self.ex.execute_function(
            'decimal_test',
            'store_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty',
                'f': Decimal('6.6')
            }
        )

        f = self.ex.execute_function(
            'decimal_test',
            'divide_float',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                's': 'floaty',
            }
        )

        self.assertEqual(f['output'], Decimal('3.3'))
