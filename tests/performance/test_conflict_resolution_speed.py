from unittest import TestCase
from unittest.mock import MagicMock
from seneca.engine.client import *
from seneca.engine.interface import SenecaInterface
from seneca.libs.logger import overwrite_logger_level
import time, random


GENESIS_AUTHOR = 'davis'


XFER_CODE_STR = """ \

from seneca.contracts.currency import transfer
transfer('{receiver}', {amount})
"""


MINT_CODE_STR = """ \
from seneca.contracts.currency import mint
mint({}, {})
"""

CONTRACTS_TO_STORE = {'currency': 'kv_currency.sen.py'}
NUM_WALLETS = 10 ** 5
SEED_AMOUNT = 10 ** 6
PERSON_A = 'conflictor_a'
PERSON_B = 'conflictor_b'


class MockContract:
    def __init__(self, sender: str, code: str, contract_name: str):
        self.sender, self.code, self.contract_name = sender, code, contract_name


def setup():
    # overwrite_logger_level(0)
    with SenecaInterface(False) as interface:
        interface.r.flushall()

        # Store all smart contracts in CONTRACTS_TO_STORE
        import seneca
        test_contracts_path = seneca.__path__[0] + '/../test_contracts/'

        for contract_name, file_name in CONTRACTS_TO_STORE.items():
            with open(test_contracts_path + file_name) as f:
                code_str = f.read()
                interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str, keep_original=True)

        start = time.time()
        print("------ MINTING -------")
        print("Minting {} wallets...".format(NUM_WALLETS))
        for i in range(NUM_WALLETS):
            interface.execute_function(module_path='seneca.contracts.currency.mint',
                                       sender=GENESIS_AUTHOR, to=str(i), amount=SEED_AMOUNT, stamps=1000)
        for w in (PERSON_A, PERSON_B):
            interface.execute_function(module_path='seneca.contracts.currency.mint',
                                       sender=GENESIS_AUTHOR, to=w, amount=SEED_AMOUNT, stamps=1000)
        print("Finished minting wallet in {} seconds".format(round(time.time()-start, 2)))
        print("----------------------")


def create_currency_tx(sender: str, receiver: str, amount: int, contract_name: str='currency'):
    code = XFER_CODE_STR.format(receiver=receiver, amount=amount)
    contract = MockContract(sender=sender, code=code, contract_name=contract_name)
    return contract


def test_baseline(num_contracts: int=30000):
    start = time.time()
    print(" ----- BASELINE ------")
    print("Running {} contracts with random addresses...".format(num_contracts))
    with SenecaInterface(False) as interface:
        for i in range(num_contracts):
            amount = 1
            sender, receiver = random.sample(range(NUM_WALLETS), 2)
            interface.execute_function(module_path='seneca.contracts.currency.transfer',
                                       sender=str(sender), to=str(receiver), amount=amount, stamps=1000)
    dur = time.time()-start
    print("Finished running baseline contracts in {} seconds ".format(round(dur, 2)))
    print("Baseline TPS: {}".format(num_contracts/dur))
    print("----------------------")


if __name__ == '__main__':
    setup()

    # First, we test baseline
    test_baseline()

    # Now for the real deal

# class TestSenecaClient(TestCase):
#     CONTRACTS_TO_STORE = {'currency': 'kv_currency.sen.py'}
#
#     def setUp(self):
#         overwrite_logger_level(0)
#         with SenecaInterface(False) as interface:
#             interface.r.flushall()
#
#             # Store all smart contracts in CONTRACTS_TO_STORE
#             import seneca
#             test_contracts_path = seneca.__path__[0] + '/../test_contracts/'
#
#             for contract_name, file_name in self.CONTRACTS_TO_STORE.items():
#                 with open(test_contracts_path + file_name) as f:
#                     code_str = f.read()
#                     interface.publish_code_str(contract_name, GENESIS_AUTHOR, code_str, keep_original=True)
#
#             rt = make_n_tup({
#                 'author': GENESIS_AUTHOR,
#                 'sender': GENESIS_AUTHOR,
#             })
#             interface.execute_code_str(MINT_CODE_STR, scope={'rt': rt})
#
#     def test_setup_dbs(self):
#         client = SenecaClient(sbb_idx=0, num_sbb=1)
#
#         self.assertTrue(client.master_db is not None)
#         self.assertTrue(client.active_db is None)
#
#         self.assertEqual(len(client.available_dbs), NUM_CACHES)
#
#     def test_run_tx_increments_contract_idx(self):
#         client = SenecaClient(sbb_idx=0, num_sbb=1)
#         client._start_sb('A' * 64)
#
#         self.assertEqual(client.active_db.next_contract_idx, 0)
#
#         c1 = create_currency_tx('davis', 'stu', 14)
#         c2 = create_currency_tx('stu', 'davis', 40)
#
#         client.run_contract(c1)
#         self.assertEqual(client.active_db.next_contract_idx, 1)
#
#         client.run_contract(c2)
#         self.assertEqual(client.active_db.next_contract_idx, 2)
#
#     def test_end_subblock_1_sbb(self):
#         input_hash = 'A' * 64
#
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#         client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
#         client._start_sb(input_hash)
#
#         c1 = create_currency_tx('davis', 'stu', 14)
#         c2 = create_currency_tx('stu', 'davis', 40)
#         client.run_contract(c1)
#         client.run_contract(c2)
#
#         client._end_sb()
#         self.assertTrue(input_hash in client.pending_futures)
#
#         # We must run the future manually, since the event loop is not currently running
#         loop.run_until_complete(client.pending_futures[input_hash]['fut'])
#
#         actual_sbb_rep = client.update_master_db()
#         expected_sbb_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
#                             (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]
#         self.assertEqual(expected_sbb_rep, actual_sbb_rep)
#
#         loop.close()
#
#     def test_end_subblock_2_sbb(self):
#         input_hash1 = 'A' * 64
#         input_hash2 = 'B' * 64
#
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#         client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
#         client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
#         client1._start_sb(input_hash1)
#         client2._start_sb(input_hash2)
#
#         c1 = create_currency_tx('davis', 'stu', 14)
#         c2 = create_currency_tx('stu', 'davis', 40)
#         c3 = create_currency_tx('ghu', 'davis', 15)
#         c4 = create_currency_tx('tj', 'birb', 90)
#         client1.run_contract(c1)
#         client1.run_contract(c2)
#         client2.run_contract(c3)
#         client2.run_contract(c4)
#
#         client1._end_sb()
#         client2._end_sb()
#         self.assertTrue(input_hash1 in client1.pending_futures)
#         self.assertTrue(input_hash2 in client2.pending_futures)
#
#         # We must run the future manually, since the event loop is not currently running
#         coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
#         loop.run_until_complete(asyncio.gather(*coros))
#
#         # Check the sb rep output after merging to master on each
#         expected_sbb1_rep = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
#                              (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]
#         expected_sbb2_rep = [(c3, "SUCC", "SET balances:ghu 8985;SET balances:davis 10041;"),
#                              (c4, "SUCC", "SET balances:tj 7910;SET balances:birb 8090;")]
#         actual_sbb1_rep = client1.update_master_db()
#         actual_sbb2_rep = client2.update_master_db(False)
#         self.assertEqual(expected_sbb1_rep, actual_sbb1_rep)
#         self.assertEqual(expected_sbb2_rep, actual_sbb2_rep)
#
#         loop.close()
#
#     def test_end_subblock_2_sbb_start_subblocks_before_ending_then_flush_all_dem_bois(self):
#         input_hash1 = 'A' * 64
#         input_hash2 = 'B' * 64
#         input_hash3 = 'C' * 64
#         input_hash4 = 'D' * 64
#
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#         client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
#         client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
#
#         client1._start_sb(input_hash1)
#         client2._start_sb(input_hash2)
#
#         c1 = create_currency_tx('davis', 'stu', 14)
#         c2 = create_currency_tx('stu', 'davis', 40)
#         c3 = create_currency_tx('ghu', 'davis', 15)
#         c4 = create_currency_tx('tj', 'birb', 90)
#         client1.run_contract(c1)
#         client1.run_contract(c2)
#         client2.run_contract(c3)
#         client2.run_contract(c4)
#
#         client1._end_sb()
#         client2._end_sb()
#
#         client1._start_sb(input_hash3)
#         client2._start_sb(input_hash4)
#
#         c5 = create_currency_tx('ethan', 'birb', 60)
#         c6 = create_currency_tx('stu', 'davis', 10)
#         c7 = create_currency_tx('ghu', 'tj', 50)
#         c8 = create_currency_tx('birb', 'davis', 100)
#         client1.run_contract(c5)
#         client1.run_contract(c6)
#         client2.run_contract(c7)
#         client2.run_contract(c8)
#
#         client1._end_sb()
#         client2._end_sb()
#         self.assertTrue(input_hash1 in client1.pending_futures)
#         self.assertTrue(input_hash3 in client1.pending_futures)
#         self.assertTrue(input_hash2 in client2.pending_futures)
#         self.assertTrue(input_hash4 in client2.pending_futures)
#
#         # We must run the future manually, since the event loop is not currently running
#         coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
#         loop.run_until_complete(asyncio.gather(*coros))
#
#         # Check the sb rep output after merging to master on each
#         expected_sbb1_1 = [(c1, "SUCC", "SET balances:davis 9986;SET balances:stu 83;"),
#                            (c2, "SUCC", "SET balances:stu 43;SET balances:davis 10026;")]
#         expected_sbb2_1 = [(c3, "SUCC", "SET balances:ghu 8985;SET balances:davis 10041;"),
#                            (c4, "SUCC", "SET balances:tj 7910;SET balances:birb 8090;")]
#         expected_sbb1_2 = [(c5, "SUCC", "SET balances:ethan 7940;SET balances:birb 8150;"),
#                            (c6, "SUCC", "SET balances:stu 33;SET balances:davis 10051;")]
#         expected_sbb2_2 = [(c7, "SUCC", "SET balances:ghu 8935;SET balances:tj 7960;"),
#                            (c8, "SUCC", "SET balances:birb 8050;SET balances:davis 10151;")]
#
#         actual_sbb1_1 = client1.update_master_db(True)
#         actual_sbb2_1 = client2.update_master_db(False)
#         self.assertEqual(expected_sbb1_1, actual_sbb1_1)
#         self.assertEqual(expected_sbb2_1, actual_sbb2_1)
#
#         coros = (client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
#         loop.run_until_complete(asyncio.gather(*coros))
#
#         actual_sbb1_2 = client1.update_master_db(True)
#         actual_sbb2_2 = client2.update_master_db(False)
#         self.assertEqual(expected_sbb1_2, actual_sbb1_2)
#         self.assertEqual(expected_sbb2_2, actual_sbb2_2)
#
#         loop.close()
#
#     # Test that pending_db/active_db/working_db get updated as we go thru the flow
#
#     # Test starting a new sub block before the last sub block finishes
#
#     # Test with multiple sb's where stuff in SB 2 will pass the first time and fail the second time (cause some og read was modified)
