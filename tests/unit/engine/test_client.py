from tests.utils import TestExecutor
from unittest import mock
from seneca.engine.client import *
from seneca.engine.interpreter.parser import Parser
from seneca.libs.logger import overwrite_logger_level, get_logger
from collections import OrderedDict, defaultdict
import random, os, marshal
import ujson as json
from base64 import b64encode
from seneca.constants.config import SENECA_PATH


log = get_logger("TestSenecaClient")
GENESIS_AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
STAMP_AMOUNT = 0
MINT_WALLETS = {
    'anonymoose': 10000,
    'stu': 69,
    'birb': 8000,
    'ghu': 9000,
    'tj': 8000,
    'ethan': 8000
}

# Add a bunch of other random wallet
# for _ in range(359):
#     MINT_WALLETS[str(uuid.uuid4())] = 2 ** 63


TEST_CONTRACT = \
"""
from seneca.libs.storage.datatypes import Hash

sample = Hash('sample')

@seed
def init():
    sample['hello'] = 'world'
    
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
        self.kwargs = {'contract_name': contract_name, 'code_str': contract_code}
        self.stamps_supplied, self.sender, self.contract_name, self.func_name = stamps, sender, 'smart_contract', 'submit_contract'


def create_currency_tx(sender: str, receiver: str, amount: int, contract_name: str='currency', stamps=STAMP_AMOUNT):
    contract = MockContractTransaction(sender=sender, contract_name='currency', func_name='transfer', stamps=stamps,
                                       to=receiver, amount=amount)
    return contract


class TestSenecaClient(TestExecutor):

    LOG_LVL = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.LOG_LVL:
            overwrite_logger_level(cls.LOG_LVL)

    @classmethod
    def tearDownClass(cls):
        if cls.LOG_LVL:
            overwrite_logger_level(999999)  # re-enable all logging
        super().tearDownClass()

    def setUp(self):
        # overwrite_logger_level(0)
        self.ex = Executor(metering=False, concurrency=False)
        self.r.flushall()
        self._mint_wallets()
        self.completed_hashes = defaultdict(list)

    def assert_completion(self, expected_sbb_rep=None, input_hash='', merge_master=False, client=None, merge_wait=1):
        if merge_master:
            assert client is not None, "if merge_master=True then client must be passed in"

        async def _merge(client):
            asyncio.sleep(merge_wait)
            client.update_master_db()

        def _completion_handler(cr_data: CRContext):
            if input_hash:
                self.assertEqual(cr_data.input_hash, input_hash)
            if expected_sbb_rep:
                self.assertEqual(expected_sbb_rep, cr_data.get_subblock_rep())
            if merge_master:
                asyncio.ensure_future(_merge(client))
            if client and input_hash:
                self.completed_hashes[client].append(input_hash)

        return _completion_handler

    def _get_futures(self, input_hash_client_dict: dict) -> list:
        futs = []
        for input_hash, client in input_hash_client_dict.items():
            if input_hash in client.pending_futures:
                d = client.pending_futures[input_hash]
                futs.append(d['fut'])
                if d['merge_fut']:
                    futs.append(d['merge_fut'])
            for data in client.queued_futures:
                if data['input_hash'] == input_hash:
                    futs.append(data['fut'])

        return futs

    def _gen_random_contracts(self, num=8, max_amount=8, stamps=STAMP_AMOUNT) -> list:
        contracts = []
        for _ in range(num):
            sender, receiver = random.sample(list(MINT_WALLETS.keys()), 2)
            amount = random.randint(0, max_amount)
            contracts.append(create_currency_tx(sender, receiver, amount, stamps=stamps))

        return contracts

    def _mint_wallets(self, seed_amount=None):
        for wallet, amount in MINT_WALLETS.items():
            self.ex.execute_function('currency', 'mint', GENESIS_AUTHOR, STAMP_AMOUNT, kwargs={
                'to': wallet, 'amount': seed_amount or amount
            })

    def test_setup_dbs(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)

        self.assertTrue(client.master_db is not None)
        self.assertTrue(client.active_db is None)

        self.assertEqual(len(client.available_dbs), NUM_CACHES)

    def test_flush(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.metering = False

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)

        client._start_sb('A' * 64)
        client.run_contract(c1)
        client.run_contract(c2)

        client.flush_all()

        self.assertEqual(len(client.pending_dbs), 0)
        self.assertEqual(client.active_db, None)

        loop.close()

    def test_skip_current_db(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        input_hash = 'A' * 64
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.metering = False

        client.execute_sb(input_hash=input_hash, contracts=[c1, c2],
                          completion_handler=self.assert_completion(None, input_hash))
        self.assertTrue(input_hash in client.pending_futures)

        client.skip_current_db()
        self.assertEqual(len(client.pending_futures), 0)

        loop.close()

    def test_run_tx_increments_contract_idx(self):
        client = SenecaClient(sbb_idx=0, num_sbb=1)
        client.metering = False
        client._start_sb('A' * 64)

        self.assertEqual(client.active_db.next_contract_idx, 0)

        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)

        client.run_contract(c1)
        self.assertEqual(client.active_db.next_contract_idx, 1)

        client.run_contract(c2)
        self.assertEqual(client.active_db.next_contract_idx, 2)

    # TODO: Davis!
    # def test_with_just_a_lone_publish_transaction(self):
    #
    #     self.ex.concurrency = False
    #     code_obj, resources, methods = self.ex.compile('test', TEST_CONTRACT)
    #     contract_str = b64encode(marshal.dumps({
    #         'code_str': TEST_CONTRACT,
    #         'code_obj': code_obj,
    #         'author': "anonymoose",
    #         'resources': resources.get('test', {}),
    #         'methods': methods.get('test', {}),
    #     })).decode()
    #
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #
    #     input_hash = 'A' * 64
    #     c1 = MockPublishTransaction(sender='anonymoose', contract_name='test', contract_code=TEST_CONTRACT)
    #
    #     client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
    #     client.metering = False
    #
    #     expected_sbb_rep = [(c1, "SUCC", 'SET Hash:test:sample:hello "world";SET contracts:test ' + contract_str + ';')]
    #     client.execute_sb(input_hash, [c1], self.assert_completion(expected_sbb_rep, input_hash, merge_master=True,
    #                                                                client=client, merge_wait=0))
    #
    #     self.assertTrue(input_hash in client.pending_futures)
    #
    #     # We must run the future manually, since the event loop is not currently running
    #     loop.run_until_complete(client.pending_futures[input_hash]['fut'])
    #     loop.close()
    #
    # def test_with_just_a_lone_publish_transaction_but_two_clients_but_one_of_them_has_no_transactions(self):
    #     self.ex.concurrency = False
    #     code_obj, resources, methods = self.ex.compile('test', TEST_CONTRACT)
    #     contract_str = b64encode(marshal.dumps({
    #         'code_str': TEST_CONTRACT,
    #         'code_obj': code_obj,
    #         'author': "anonymoose",
    #         'resources': resources.get('test', {}),
    #         'methods': methods.get('test', {}),
    #     })).decode()
    #
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #
    #     input_hash1 = 'A' * 64
    #     input_hash2 = 'B' * 64
    #     c1 = MockPublishTransaction(sender='anonymoose', contract_name='test', contract_code=TEST_CONTRACT)
    #
    #     client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop, metering=False)
    #     client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop, metering=False)
    #
    #     expected_sbb_rep = [(c1, "SUCC", 'SET Hash:test:sample:hello "world";SET contracts:test ' + contract_str + ';')]
    #     client1.execute_sb(input_hash1, [], self.assert_completion(None, input_hash1, merge_master=True,
    #                        client=client1, merge_wait=0))
    #     client2.execute_sb(input_hash2, [c1], self.assert_completion(expected_sbb_rep, input_hash2, merge_master=True,
    #                        client=client2, merge_wait=0))
    #
    #     # We must run the future manually, since the event loop is not currently running
    #     loop.run_until_complete(asyncio.gather(client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut']))
    #
    #     loop.close()
    #
    # def test_with_publish_transactions(self):
    #
    #     self.ex.concurrency = False
    #     code_obj, resources, methods = self.ex.compile('test', TEST_CONTRACT)
    #     contract_str = b64encode(marshal.dumps({
    #         'code_str': TEST_CONTRACT,
    #         'code_obj': code_obj,
    #         'author': "anonymoose",
    #         'resources': resources.get('test', {}),
    #         'methods': methods.get('test', {}),
    #     })).decode()
    #
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #
    #     input_hash = 'A' * 64
    #     c1 = create_currency_tx('anonymoose', 'stu', 14)
    #     c2 = MockPublishTransaction(sender='anonymoose', contract_name='test', contract_code=TEST_CONTRACT)
    #
    #     client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
    #     client.metering = False
    #     client._start_sb(input_hash)
    #
    #     client.run_contract(c1)
    #     client.run_contract(c2)
    #
    #     expected_sbb_rep = [(c1, "SUCC",
    #                          "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
    #                         (c2, "SUCC", 'SET Hash:test:sample:hello "world";SET contracts:test ' + contract_str + ';')]
    #
    #     client._end_sb(self.assert_completion(expected_sbb_rep, input_hash))
    #     self.assertTrue(input_hash in client.pending_futures)
    #
    #     # We must run the future manually, since the event loop is not currently running
    #     loop.run_until_complete(client.pending_futures[input_hash]['fut'])
    #
    #     loop.close()

    def test_end_subblock_1_sbb(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash = 'A' * 64
        c1 = create_currency_tx('anonymoose', 'stu', 14)
        c2 = create_currency_tx('stu', 'anonymoose', 40)
        expected_sbb_rep = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                            (c2, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop, metering=False)
        client.metering = False
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
        expected_sbb_rep = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                            (c2, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.metering = False

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
        client.metering = False
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
        expected_sbb1_rep = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                             (c2, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]
        expected_sbb2_rep = []

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client1.metering = False
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client2.metering = False
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
        expected_sbb_rep = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                            (c2, "FAIL -- Sender balance must be non-negative!!!", ""),
                            (c3, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]

        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.metering = False
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
        expected_sbb1_rep = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                             (c2, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]
        expected_sbb2_rep = [(c3, "SUCC", "SET DecimalHash:currency:balances:ghu 8985.0;SET DecimalHash:currency:balances:anonymoose 10041.0;"),
                             (c4, "SUCC", "SET DecimalHash:currency:balances:tj 7910.0;SET DecimalHash:currency:balances:birb 8090.0;")]

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client1.metering = False
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client2.metering = False
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
        expected_sbb1_1 = [(c1, "SUCC", "SET DecimalHash:currency:balances:anonymoose 9986.0;SET DecimalHash:currency:balances:stu 83.0;"),
                           (c2, "SUCC", "SET DecimalHash:currency:balances:stu 43.0;SET DecimalHash:currency:balances:anonymoose 10026.0;")]
        expected_sbb2_1 = [(c3, "SUCC", "SET DecimalHash:currency:balances:ghu 8985.0;SET DecimalHash:currency:balances:anonymoose 10041.0;"),
                           (c4, "SUCC", "SET DecimalHash:currency:balances:tj 7910.0;SET DecimalHash:currency:balances:birb 8090.0;")]
        expected_sbb1_2 = [(c5, "SUCC", "SET DecimalHash:currency:balances:ethan 7940.0;SET DecimalHash:currency:balances:birb 8150.0;"),
                           (c6, "SUCC", "SET DecimalHash:currency:balances:stu 33.0;SET DecimalHash:currency:balances:anonymoose 10051.0;")]
        expected_sbb2_2 = [(c7, "SUCC", "SET DecimalHash:currency:balances:ghu 8935.0;SET DecimalHash:currency:balances:tj 7960.0;"),
                           (c8, "SUCC", "SET DecimalHash:currency:balances:birb 8050.0;SET DecimalHash:currency:balances:anonymoose 10151.0;")]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client1.metering = False
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client2.metering = False

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
        client1.metering = False
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client2.metering = False

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
        coros1 = self._get_futures({input_hash1: client1, input_hash2: client2})
        # coros1 = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'],
        #          client1.pending_futures[input_hash3]['fut'])
        loop.run_until_complete(asyncio.gather(*coros1))

        client2.update_master_db()
        client1.update_master_db()

        # coros2 = (client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
        coros2 = self._get_futures({input_hash3: client1, input_hash4: client2})
        loop.run_until_complete(asyncio.gather(*coros2))

        for c in (client1, client2):
            all_input_hashes = [cr.input_hash for cr in c.pending_dbs]
            self.assertEqual(len(c.pending_dbs), 0, "Client with sbb_idx {} has pending_dbs: {}".format(c.sbb_idx, all_input_hashes))

        loop.close()

    @mock.patch("seneca.engine.client.NUM_CACHES", 2)
    def test_hella_subblocks_with_stamps(self):
        self._mint_wallets(10 ** 8)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash1 = '1' * 64
        input_hash2 = '2' * 64
        input_hash3 = '3' * 64
        input_hash4 = '4' * 64
        input_hash5 = '5' * 64
        input_hash6 = '6' * 64
        input_hash7 = '7' * 64
        input_hash8 = '8' * 64
        input_hash9 = 'A' * 64
        input_hash10 = 'B' * 64

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)

        c1_map = OrderedDict({input_hash1: client1, input_hash3: client1, input_hash5: client1, input_hash7: client1})
        c2_map = OrderedDict({input_hash2: client2, input_hash4: client2, input_hash6: client2, input_hash8: client2})

        NUM_TX = 10
        for i, in_hash in enumerate(c1_map):
            # txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if i % 2 == 1 else []
            txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if True else []
            client1.execute_sb(in_hash, txs, self.assert_completion(None, in_hash, merge_master=True, client=client1, merge_wait=0))
        for i, in_hash in enumerate(c2_map):
            # txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if i % 2 == 1 else []
            txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if True else []
            client2.execute_sb(in_hash, txs, self.assert_completion(None, in_hash, merge_master=True, client=client2, merge_wait=0))

        # Execute an empty sb at the end
        client1.execute_sb(input_hash9, [], self.assert_completion(None, input_hash9, merge_master=True, client=client1, merge_wait=0))
        client2.execute_sb(input_hash10, [], self.assert_completion(None, input_hash10, merge_master=True, client=client2, merge_wait=0))

        # Run it all
        coros1 = self._get_futures(c1_map)
        coros2 = self._get_futures(c2_map)

        loop.run_until_complete(asyncio.gather(*coros1, *coros2))

        async def _wait_for_things_to_finish():
            log.notice("Tester waiting for things to finish")
            await asyncio.sleep(3)
            log.notice("Tester done waiting")

        loop.run_until_complete(_wait_for_things_to_finish())
        loop.close()

    @mock.patch("seneca.engine.client.NUM_CACHES", 2)
    def test_hella_subblocks_called_in_correct_order(self):
        self._mint_wallets(10 ** 8)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        input_hash1 = '1' * 64
        input_hash2 = '2' * 64
        input_hash3 = '3' * 64
        input_hash4 = '4' * 64
        input_hash5 = '5' * 64
        input_hash6 = '6' * 64
        input_hash7 = '7' * 64
        input_hash8 = '8' * 64
        input_hash9 = 'A' * 64
        input_hash10 = 'B' * 64

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)

        c1_map = OrderedDict({input_hash1: client1, input_hash3: client1, input_hash5: client1, input_hash7: client1})
        c2_map = OrderedDict({input_hash2: client2, input_hash4: client2, input_hash6: client2, input_hash8: client2})

        NUM_TX = 23
        for i, in_hash in enumerate(c1_map):
            # txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if i % 2 == 1 else []
            txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if True else []
            client1.execute_sb(in_hash, txs, self.assert_completion(None, in_hash, merge_master=True, client=client1, merge_wait=0))
        for i, in_hash in enumerate(c2_map):
            # txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if i % 2 == 1 else []
            txs = self._gen_random_contracts(num=NUM_TX, stamps=10 ** 5) if True else []
            client2.execute_sb(in_hash, txs, self.assert_completion(None, in_hash, merge_master=True, client=client2, merge_wait=0))

        # Execute an empty sb at the end
        client1.execute_sb(input_hash9, [], self.assert_completion(None, input_hash9, merge_master=True, client=client1, merge_wait=0))
        client2.execute_sb(input_hash10, [], self.assert_completion(None, input_hash10, merge_master=True, client=client2, merge_wait=0))

        # Run it all
        coros1 = self._get_futures(c1_map)
        coros2 = self._get_futures(c2_map)

        loop.run_until_complete(asyncio.gather(*coros1, *coros2))

        async def _wait_for_things_to_finish():
            log.notice("Tester waiting for things to finish")
            await asyncio.sleep(3)
            log.notice("Tester done waiting")

        loop.run_until_complete(_wait_for_things_to_finish())
        loop.close()

        # Check things were called in the correct order
        self.assertEqual(list(c1_map.keys()) + [input_hash9], self.completed_hashes[client1])
        self.assertEqual(list(c2_map.keys()) + [input_hash10], self.completed_hashes[client2])

    def test_contract_with_key_that_doesnt_exist_yet(self):
        self._mint_wallets(10 ** 8)

        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64
        input_hash3 = 'C' * 64
        input_hash4 = 'D' * 64

        stamps = 10**4
        c1 = create_currency_tx('anonymoose', 'stu', 14, stamps=stamps)
        c2 = create_currency_tx('stu', 'anonymoose', 40, stamps=stamps)
        c3 = create_currency_tx('ghu', 'A NEW KEY THAT DOESNT EXIST', 10**9, stamps=stamps)
        c4 = create_currency_tx('tj', 'birb', 90, stamps=stamps)
        c5 = create_currency_tx('ethan', 'birb', 60, stamps=stamps)
        c6 = create_currency_tx('stu', 'anonymoose', 10, stamps=stamps)
        c7 = create_currency_tx('ghu', 'tj', 50, stamps=stamps)
        c8 = create_currency_tx('birb', 'anonymoose', 100, stamps=stamps)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client1 = SenecaClient(sbb_idx=0, num_sbb=2, loop=loop)
        client1.metering = False
        client2 = SenecaClient(sbb_idx=1, num_sbb=2, loop=loop)
        client2.metering = False

        client1.execute_sb(input_hash1, contracts=[c1, c2], completion_handler=self.assert_completion(None, input_hash1))
        client2.execute_sb(input_hash2, contracts=[c3, c4], completion_handler=self.assert_completion(None, input_hash2))

        client1.execute_sb(input_hash3, contracts=[c5, c6], completion_handler=self.assert_completion(None, input_hash3))
        client2.execute_sb(input_hash4, contracts=[c7, c8], completion_handler=self.assert_completion(None, input_hash4))

        client1.update_master_db()
        client2.update_master_db()

        # We must run the future manually, since the event loop is not currently running
        coros = (client1.pending_futures[input_hash1]['fut'], client2.pending_futures[input_hash2]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        coros = (client1.pending_futures[input_hash3]['fut'], client2.pending_futures[input_hash4]['fut'])
        loop.run_until_complete(asyncio.gather(*coros))

        loop.close()

    @mock.patch("seneca.engine.client.NUM_CACHES", 2)
    def test_publish_tx_then_use_that_tx_with_one_sb_builder(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = SenecaClient(sbb_idx=0, num_sbb=1, loop=loop)
        client.metering = False

        contract_name = 'stubucks'
        input_hash1 = '1' * 64
        input_hash2 = '2' * 64
        input_hash3 = '3' * 64
        input_hash4 = '4' * 64

        with open(os.path.join(os.path.dirname(SENECA_PATH), 'test_contracts', 'stubucks.sen.py'), 'r') as f:
            code = f.read()

        # print("got contract code {}".format(code))
        publish_tx = MockPublishTransaction(sender=MINT_WALLETS['stu'], contract_name=contract_name, contract_code=code)
        transfer_tx = MockContractTransaction(sender='435e3264395e24eb37a0eb6c322421e701dc332db45536d25eac67924b9321aa',
                                              contract_name=contract_name, func_name='transfer', to=MINT_WALLETS['birb'], amount=1)

        tx1_set = self._gen_random_contracts(num=7) + [publish_tx]
        tx2_set = self._gen_random_contracts(num=7) + [transfer_tx]
        tx3_set = []
        tx4_set = self._gen_random_contracts(num=10)

        client.execute_sb(input_hash1, contracts=tx1_set, completion_handler=self.assert_completion(None, input_hash1, merge_master=True, client=client))
        client.execute_sb(input_hash2, contracts=tx2_set, completion_handler=self.assert_completion(None, input_hash2, merge_master=True, client=client))
        client.execute_sb(input_hash3, contracts=tx3_set, completion_handler=self.assert_completion(None, input_hash3, merge_master=True, client=client))
        client.execute_sb(input_hash4, contracts=tx4_set, completion_handler=self.assert_completion(None, input_hash4, merge_master=True, client=client))

        coros = self._get_futures(OrderedDict({input_hash1: client, input_hash2: client, input_hash3: client, input_hash4: client}))
        loop.run_until_complete(asyncio.gather(*coros))

        async def _wait_for_things_to_finish():
            log.notice("Tester waiting for things to finish")
            await asyncio.sleep(1)
            log.notice("Tester done waiting")

        loop.run_until_complete(_wait_for_things_to_finish())
        loop.close()

    # Test with multiple sb's where stuff in SB 2 will pass the first time and fail the second time (cause some og read was modified)


if __name__ == "__main__":
    import unittest
    unittest.main()
