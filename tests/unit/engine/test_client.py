from unittest import TestCase
from unittest.mock import MagicMock
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.libs.logger import overwrite_logger_level


GENESIS_AUTHOR = 'davis'


XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('{receiver}', {amount})
"""


MINT_CODE_STR = """ \

from seneca.contracts.currency import mint
mint('davis', 10000)
mint('stu', 69)
mint('birb', 8000)
mint('ghu', 9000)
mint('tj', 8000)
mint('ethan', 8000)
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

    def assert_completion(self, expected_sbb_rep: List[tuple]=None, input_hash=''):
        def _completion_handler(cr_data: CRContext):
            if input_hash:
                self.assertEqual(cr_data.input_hash, input_hash)
            if expected_sbb_rep:
                self.assertEqual(expected_sbb_rep, cr_data.get_subblock_rep())

        return _completion_handler

    def setUp(self):
        # overwrite_logger_level(0)
        with SenecaInterface(False) as interface:
            interface.r.flushall()
            # Store all smart contracts in CONTRACTS_TO_STORE
            import seneca
            test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

            for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
                with open(test_contracts_path + file_name) as f:
                    code_str = f.read()
                    interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str, keep_original=True)

            rt = {
                'author': GENESIS_AUTHOR,
                'sender': GENESIS_AUTHOR,
                'contract': 'minter'
            }
            interface.execute_code_str(MINT_CODE_STR, scope={'rt': rt})

    def test_setup_dbs(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES)

    def test_flush(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)

        client._start_sb('A' * 64)
        client.run_contract(c1)
        client.run_contract(c2)

        client.flush_all()

        self.assertEqual(len(client.pending_dbs), 0)
        self.assertEqual(client.active_db, None)

    def test_run_tx_increments_contract_idx(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)
        client._start_sb('A' * 64)

        self.assertEqual(client.active_db.next_contract_idx, 0)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)

        client.run_contract(c1)
        self.assertEqual(client.active_db.next_contract_idx, 1)

        client.run_contract(c2)
        self.assertEqual(client.active_db.next_contract_idx, 2)

    def test_end_subblock_1_sbb(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
                            (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client._start_sb(input_hash)

        client.run_contract(c1)
        client.run_contract(c2)

        client._end_sb(self.assert_completion(expected_sbb_rep, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        loop.close()

    def test_execute_sb(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
                            (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)

        client.execute_sb(input_hash=input_hash, contracts=[c1, c2],
                          completion_handler=self.assert_completion(expected_sbb_rep, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        loop.close()

    def test_end_subblock_1_sbb_with_failure(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 9000)
        c3 = create_currency_tx('stu', 'davis', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
                            (c2, "FAIL -- Sender balance must be non-negative!!!", ""),
                            (c3, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client._start_sb(input_hash)

        client.run_contract(c1)
        client.run_contract(c2)
        client.run_contract(c3)

        client._end_sb(self.assert_completion(expected_sbb_rep, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        loop.close()

    def test_end_subblock_2_sbb(self):
        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        c3 = create_currency_tx('ghu', 'davis', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        expected_sbb1_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
                             (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]
        expected_sbb2_rep = [(c3, "SUCC", "SET balances:ghu 8985;SET balances:davis 10041;"),
                             (c4, "SUCC", "SET balances:tj 7910;SET balances:birb 8090;")]

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client1._start_sb(input_hash1)
        client2._start_sb(input_hash2)

        client1.run_contract(c1)
        client1.run_contract(c2)
        client2.run_contract(c3)
        client2.run_contract(c4)

        client1._end_sb(self.assert_completion(expected_sbb1_rep, input_hash1))
        client2._end_sb(self.assert_completion(expected_sbb2_rep, input_hash2))
        self.assertTrue(input_hash1 in client1.pending_futures)
        self.assertTrue(input_hash2 in client2.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        loop.close()

    def test_end_subblock_2_sbb_start_subblocks_before_ending_then_flush_all_dem_bois(self):
        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64
        input_hash3 = 'C' * 64
        input_hash4 = 'D' * 64

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        c3 = create_currency_tx('ghu', 'davis', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        c5 = create_currency_tx('ethan', 'birb', 60)
        c6 = create_currency_tx('stu', 'davis', 10)
        c7 = create_currency_tx('ghu', 'tj', 50)
        c8 = create_currency_tx('birb', 'davis', 100)
        expected_sbb1_1 = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
                           (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]
        expected_sbb2_1 = [(c3, "SUCC", "SET balances:ghu 8985;SET balances:davis 10041;"),
                           (c4, "SUCC", "SET balances:tj 7910;SET balances:birb 8090;")]
        expected_sbb1_2 = [(c5, "SUCC", "SET balances:ethan 7940;SET balances:birb 8150;"),
                           (c6, "SUCC", "SET balances:stu 33;SET balances:davis 10051;")]
        expected_sbb2_2 = [(c7, "SUCC", "SET balances:ghu 8935;SET balances:tj 7960;"),
                           (c8, "SUCC", "SET balances:birb 8050;SET balances:davis 10151;")]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)

        client1._start_sb(input_hash1)
        client2._start_sb(input_hash2)

        client1.run_contract(c1)
        client1.run_contract(c2)
        client2.run_contract(c3)
        client2.run_contract(c4)

        client1._end_sb(self.assert_completion(expected_sbb1_1, input_hash1))
        client2._end_sb(self.assert_completion(expected_sbb2_1, input_hash2))

        client1._start_sb(input_hash3)
        client2._start_sb(input_hash4)

        client1.run_contract(c5)
        client1.run_contract(c6)
        client2.run_contract(c7)
        client2.run_contract(c8)

        client1._end_sb(self.assert_completion(expected_sbb1_2, input_hash3))
        client2._end_sb(self.assert_completion(expected_sbb2_2, input_hash4))

        self.assertTrue(input_hash1 in client1.pending_futures)
        self.assertTrue(input_hash3 in client1.pending_futures)
        self.assertTrue(input_hash2 in client2.pending_futures)
        self.assertTrue(input_hash4 in client2.pending_futures)

        client1.update_master_db(input_hash1)
        client2.update_master_db(input_hash2)

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        coros = (client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        loop.close()

    def test_update_master_db_with_incomplete_sb(self):
        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64
        input_hash3 = 'C' * 64
        input_hash4 = 'D' * 64

        c1 = create_currency_tx('davis', 'stu', 14)
        c2 = create_currency_tx('stu', 'davis', 40)
        c3 = create_currency_tx('ghu', 'davis', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        c5 = create_currency_tx('ethan', 'birb', 60)
        c6 = create_currency_tx('stu', 'davis', 10)
        c7 = create_currency_tx('ghu', 'tj', 50)
        c8 = create_currency_tx('birb', 'davis', 100)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)

        client1._start_sb(input_hash1)
        client2._start_sb(input_hash2)

        client1.run_contract(c1)
        client1.run_contract(c2)
        client2.run_contract(c3)
        client2.run_contract(c4)

        client1._end_sb(self.assert_completion(None, input_hash1))
        client2._end_sb(self.assert_completion(None, input_hash2))

        client1._start_sb(input_hash3)
        client2._start_sb(input_hash4)

        client1.run_contract(c5)
        client1.run_contract(c6)
        client2.run_contract(c7)
        client2.run_contract(c8)

        client1._end_sb(self.assert_completion(None, input_hash3))
        client2._end_sb(self.assert_completion(None, input_hash4))

        client1.update_master_db(input_hash1)
        client2.update_master_db(input_hash2)
        client1.update_master_db(input_hash3)
        client2.update_master_db(input_hash4)

        self.assertTrue(input_hash1 in client1.pending_futures)
        self.assertTrue(input_hash3 in client1.pending_futures)
        self.assertTrue(input_hash2 in client2.pending_futures)
        self.assertTrue(input_hash4 in client2.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'],
                 client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        for c in (client1, client2):
            self.assertEqual(len(c.pending_dbs), 0)

        loop.close()

    # Test that pending_db/active_db/working_db get updated as we go thru the flow

    # Test starting a new sub block before the last sub block finishes

    # Test with multiple sb's where stuff in SB 2 will pass the first time and fail the second time (cause some og read was modified)
