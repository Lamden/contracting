from unittest import TestCase
from unittest.mock import MagicMock
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
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES)

    def test_run_tx_increments_contract_idx(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)
        client.start_sub_block('A' * 64)

        self.assertEqual(client.active_db.next_contract_idx, 0)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)

        client.run_contract(c1)
        self.assertEqual(client.active_db.next_contract_idx, 1)

        client.run_contract(c2)
        self.assertEqual(client.active_db.next_contract_idx, 2)

    def test_end_subblock_1_sbb(self):
        def assert_completion_handler(data: CRDataContainer):
            self.assertTrue(len(data.contracts) == expected_num_runs)
            self.assertTrue(len(data.run_results) == expected_num_runs)
            self.assertEqual(data.run_results, expected_run_results)

        expected_run_results = ['SUCC', 'SUCC']
        expected_num_runs = 2
        input_hash = 'A' * 64
        mock_handler = MagicMock()
        mock_handler.side_effect = assert_completion_handler

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.start_sub_block(input_hash)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        client.run_contract(c1)
        client.run_contract(c2)

        client.end_sub_block(mock_handler)
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        # self.assertTrue(complete_handler_called)
        mock_handler.assert_called()

    def test_end_subblock_2_sbb(self):
        def assert_completion_handler1(data: CRDataContainer):
            self.assertTrue(len(data.contracts) == expected_num_runs)
            self.assertTrue(len(data.run_results) == expected_num_runs)
            self.assertEqual(data.run_results, expected_run_results)

        expected_run_results = ['SUCC', 'SUCC']
        expected_num_runs = 2
        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()
        mock_handler1.side_effect = assert_completion_handler1
        mock_handler2.side_effect = assert_completion_handler1

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client1.start_sub_block(input_hash1)
        client2.start_sub_block(input_hash2)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        c3 = create_currency_tx('stu', 'davis', 15)
        c4 = create_currency_tx('davis', 'stu', 90)
        client1.run_contract(c1)
        client1.run_contract(c2)
        client2.run_contract(c3)
        client2.run_contract(c4)

        client1.end_sub_block(mock_handler1)
        client2.end_sub_block(mock_handler2)
        self.assertTrue(input_hash1 in client1.pending_futures)
        self.assertTrue(input_hash2 in client2.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        mock_handler1.assert_called()
        mock_handler2.assert_called()

