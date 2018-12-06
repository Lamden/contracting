from unittest import TestCase
from unittest.mock import MagicMock
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.libs.logger import overwrite_logger_level
from decimal import Decimal


GENESIS_AUTHOR = 'anonymoose'
STAMP_AMOUNT = None
MINT_WALLETS = {
    'anonymoose': 10000,
    'stu': 69,
    'birb': 8000,
    'ghu': 9000,
    'tj': 8000,
    'ethan': 8000
}


TEST_CONTRACT = \
"""
balances = {'hello': 'world'}
@export
def one_you_can_export():
    print('Running one_you_can_export()')
@export
def one_you_can_also_export():
    print('Running one_you_can_also_export()')
    one_you_can_export()
def one_you_cannot_export(dont, do, it='wrong'):
    print('Always runs: Running one_you_cannot_export()')
@export
def one_you_can_also_also_export():
    print('Running one_you_can_also_also_export()')
    one_you_cannot_export('a', 'b', it='c')
"""


class MockContractTransaction:
    def __init__(self, sender: str, contract_name: str, func_name: str, stamps=STAMP_AMOUNT, **kwargs):
        self.stamps_supplied, self.sender, self.func_name, self.contract_name = stamps, sender, func_name, contract_name
        self.kwargs = kwargs


class MockPublishTransaction:
    def __init__(self, sender: str, contract_name: str, contract_code: str, stamps=STAMP_AMOUNT):
        self.stamps, self.sender, self.contract_code, self.contract_name = stamps, sender, contract_code, contract_name


def create_currency_tx(sender: str, receiver: str, amount: int, contract_name: str='currency'):
    contract = MockContractTransaction(sender=sender, contract_name='currency', func_name='transfer', to=receiver,
                                       amount=amount)
    return contract


class TestSenecaClient(TestCase):
    CONTRACTS_TO_STORE = {'currency': 'currency.sen.py'}

    def assert_completion(self, expected_sbb_rep: List[tuple]=None, input_hash=''):
        def _completion_handler(cr_data: CRContext):
            if input_hash:
                self.assertEqual(cr_data.input_hash, input_hash)
            if expected_sbb_rep:
                self.assertEqual(expected_sbb_rep, cr_data.get_subblock_rep())

        return _completion_handler

    def get_futures(self, input_hash_client_dict: dict) -> list:
        futs = []
        for input_hash, client in input_hash_client_dict.items():
            if input_hash in client.pending_futures:
                d = client.pending_futures[input_hash]
                futs.append(d['fut'])
                if d['merge_fut']:
                    futs.append(d['merge_fut'])
            if input_hash in client.queued_futures:
                futs.append(client.queued_futures[input_hash])

        return futs

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
                    interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str)

            rt = {
                'sender': GENESIS_AUTHOR,
                'contract': 'minter'
            }
            # tooling.execute_code_str(MINT_CODE_STR, scope={'rt': rt})
            for wallet, amount in MINT_WALLETS.items():
                interface.execute_function(module_path='seneca.contracts.currency.mint', sender=GENESIS_AUTHOR,
                                           stamps=STAMP_AMOUNT, to=wallet, amount=amount)

    def test_setup_dbs(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES)

    def test_flush(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)

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

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)

        client.run_contract(c1)
        self.assertEqual(client.active_db.next_contract_idx, 1)

        client.run_contract(c2)
        self.assertEqual(client.active_db.next_contract_idx, 2)

    def test_with_publish_transactions(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = MockPublishTransaction(sender='anonymoose', contract_name='test', contract_code=TEST_CONTRACT)
        expected_sbb_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                            (c2, "SUCC", "")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client._start_sb(input_hash)

        client.run_contract(c1)
        client.run_contract(c2)

        client._end_sb(self.assert_completion(expected_sbb_rep, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        loop.close()

    def test_end_subblock_1_sbb(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                            (c2, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]

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
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                            (c2, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)

        client.execute_sb(input_hash=input_hash, contracts=[c1, c2],
                          completion_handler=self.assert_completion(expected_sbb_rep, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        # We must run the future manually, since the event loop is not currently running
        loop.run_until_complete(client.pending_futures[input_hash]['fut'])

        loop.close()

    def test_execute_empty_sb(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        expected_sbb_rep = []
        input_hash = 'A' * 64

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.execute_sb(input_hash=input_hash, contracts=[],
                          completion_handler=self.assert_completion(expected_sbb_rep, input_hash))

        loop.run_until_complete(client.pending_futures[input_hash]['fut'])
        loop.close()

    def test_two_sb_one_empty_one_not(self):
        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        expected_sbb1_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                             (c2, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]
        expected_sbb2_rep = []

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client1.execute_sb(input_hash=input_hash1, contracts=[c1, c2], completion_handler=self.assert_completion(expected_sbb1_rep, input_hash1))
        client2.execute_sb(input_hash=input_hash2, contracts=[], completion_handler=self.assert_completion(expected_sbb2_rep, input_hash2))

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))
        loop.close()

    def test_end_subblock_1_sbb_with_failure(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 9000)
        c3 = create_currency_tx('stu', 'anonymoose', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                            (c2, "FAIL -- Sender balance must be non-negative!!!", ""),
                            (c3, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]

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

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        c3 = create_currency_tx('ghu', 'anonymoose', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        expected_sbb1_rep = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                             (c2, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]
        expected_sbb2_rep = [(c3, "SUCC", "SET currency:balances:ghu 8985;SET currency:balances:anonymoose 10041;"),
                             (c4, "SUCC", "SET currency:balances:tj 7910;SET currency:balances:birb 8090;")]

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

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        c3 = create_currency_tx('ghu', 'anonymoose', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        c5 = create_currency_tx('ethan', 'birb', 60)
        c6 = create_currency_tx('stu', 'anonymoose', 10)
        c7 = create_currency_tx('ghu', 'tj', 50)
        c8 = create_currency_tx('birb', 'anonymoose', 100)
        expected_sbb1_1 = [(c1, "SUCC", "SET currency:balances:anonymoose 9986;SET currency:balances:stu 83;"),
                           (c2, "SUCC", "SET currency:balances:stu 43;SET currency:balances:anonymoose 10026;")]
        expected_sbb2_1 = [(c3, "SUCC", "SET currency:balances:ghu 8985;SET currency:balances:anonymoose 10041;"),
                           (c4, "SUCC", "SET currency:balances:tj 7910;SET currency:balances:birb 8090;")]
        expected_sbb1_2 = [(c5, "SUCC", "SET currency:balances:ethan 7940;SET currency:balances:birb 8150;"),
                           (c6, "SUCC", "SET currency:balances:stu 33;SET currency:balances:anonymoose 10051;")]
        expected_sbb2_2 = [(c7, "SUCC", "SET currency:balances:ghu 8935;SET currency:balances:tj 7960;"),
                           (c8, "SUCC", "SET currency:balances:birb 8050;SET currency:balances:anonymoose 10151;")]

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

        client1.update_master_db()
        client2.update_master_db()

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

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        c3 = create_currency_tx('ghu', 'anonymoose', 15)
        c4 = create_currency_tx('tj', 'birb', 90)
        c5 = create_currency_tx('ethan', 'birb', 60)
        c6 = create_currency_tx('stu', 'anonymoose', 10)
        c7 = create_currency_tx('ghu', 'tj', 50)
        c8 = create_currency_tx('birb', 'anonymoose', 100)

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

        self.assertTrue(input_hash1 in client1.pending_futures)
        self.assertTrue(input_hash3 in client1.pending_futures)
        self.assertTrue(input_hash2 in client2.pending_futures)
        self.assertTrue(input_hash4 in client2.pending_futures)

        client1.update_master_db()
        client2.update_master_db()

        # We must run the future manually, since the event loop is not currently running
        # coros1 = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        coros1 = self.get_futures({input_hash1: client1, input_hash2: client2})
        # coros1 = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'],
        #          client1.pending_futures[input_hash3]['fut'])
        loop.run_until_complete(asyncio.gather(*coros1))

        client2.update_master_db()
        client1.update_master_db()

        # coros2 = (client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
        coros2 = self.get_futures({input_hash3: client1, input_hash4: client2})
        loop.run_until_complete(asyncio.gather(*coros2))

        for c in (client1, client2):
            all_input_hashes = [cr.input_hash for cr in c.pending_dbs]
            self.assertEqual(len(c.pending_dbs), 0, "Client with sbb_idx {} has pending_dbs: {}".format(c.sbb_idx, all_input_hashes))

        loop.close()


    # Test that pending_db/active_db/working_db get updated as we go thru the flow

    # Test starting a new sub block before the last sub block finishes

    # Test with multiple sb's where stuff in SB 2 will pass the first time and fail the second time (cause some og read was modified)

if __name__ == "__main__":
    import unittest
    unittest.main()
