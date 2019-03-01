from tests.utils import TestExecutor
import seneca, os

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


class TestDynamicExecution(TestExecutor):
    CONTRACTS_TO_STORE = {
        'birb_bucks': 'birb_bucks.sen.py',
        'cat_cash': 'cat_cash.sen.py'
    }

    def setUp(self):
        for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                self.ex.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)

    def test_import(self):
        os.environ['IS_IMPORT'] = 'TTTT'
        f = self.ex.execute_function(
            'smart_contract', 'execute_function',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                'contract_name': 'birb_bucks',
                'func_name': 'balance_of',
                'kwargs': {
                    'wallet_id': 'birb'
                }
            }
        )

        self.assertEqual(f['output'], 1000000)

        f = self.ex.execute_function(
            'smart_contract', 'execute_function',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                'contract_name': 'cat_cash',
                'func_name': 'balance_of',
                'kwargs': {
                    'wallet_id': 'cat'
                }
            }
        )

        self.assertEqual(f['output'], 1000000)

        f = self.ex.execute_function(
            'smart_contract', 'execute_function',
            sender=GENESIS_AUTHOR,
            stamps=None,
            kwargs={
                'contract_name': 'cat_cash',
                'func_name': 'balance_of',
                'kwargs': {
                    'wallet_id': 'birb'
                }
            }
        )

        self.assertEqual(f['output'], 0)
        os.environ['IS_IMPORT'] = ''

