from unittest import TestCase
from contracting.execution.executor import Executor
from contracting.db.cr.client import SubBlockClient
from contracting.db.driver import ContractDriver
from contracting.db.cr.callback_data import ExecutionData, SBData
from contracting.logger import get_logger
import asyncio, glob
from typing import List


class PayloadStub:
    def __init__(self, sender, contract_name, func_name, kwargs, stampsSupplied=1000000):
        self.sender = sender
        self.contractName = contract_name
        self.functionName = func_name
        self.kwargs = kwargs
        self.stampsSupplied = stampsSupplied


class TransactionStub:
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender, contract_name, func_name, kwargs)


driver = ContractDriver(db=0)
MINT_WALLETS = {
    'anonymoose': 10000,
    'stu': 69,
    'birb': 8000,
    'ghu': 9000,
    'tj': 8000,
    'ethan': 8000
}


class TestSBClient(TestCase):

    def setUp(self):
        # Add submission contract
        self.author = b'unittest'
        self.log = get_logger("TestSBClient")
        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        driver.set_contract(name='submission',
                            code=contract)
        driver.set('currency.balances:unittest', 1000000)
        driver.commit()

        # Use executor submit
        e = Executor(metering=False)
        contracts = glob.glob('./test_sys_contracts/*.py')
        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            e.execute(sender=self.author, contract_name='submission', function_name='submit_contract',
                      kwargs={'name': name, 'code': code})

        num_clients = 2
        self.clients = []
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        for i in range(num_clients):
            self.clients.append(SubBlockClient(i, num_clients, self.loop))

    def tearDown(self):
        driver.flush()
        for client in self.clients:
            client.flush_all()

    def run_loop(self, period=1):
        async def run():
            await asyncio.sleep(period)

        self.loop.run_until_complete(run())

    def test_some_conflicts(self):
        def _assert_handler1(sb_idx: int, sb_data: SBData):
            contract1 = sb_data.tx_data[0].contract 
            status1 = sb_data.tx_data[0].status 
            result1 = sb_data.tx_data[0].response 
            state1 = sb_data.tx_data[0].state 

            contract2 = sb_data.tx_data[1].contract 
            status2 = sb_data.tx_data[1].status 
            result2 = sb_data.tx_data[1].response 
            state2 = sb_data.tx_data[1].state 

            self.assertEqual(contract1, tx1)
            self.assertEqual(contract2, tx2)
            self.assertEqual(status1, 0)
            self.assertEqual(status2, 0)
            self.assertEqual(result1, 'tx1_succ')
            self.assertEqual(result2, 'tx2_succ')
            self.assertEqual(state1, '{}')
            self.assertEqual(state2, '{}')

        def _assert_handler2(sb_idx: int, sb_data: SBData):
            contract1 = sb_data.tx_data[0].contract 
            status1 = sb_data.tx_data[0].status 
            result1 = sb_data.tx_data[0].response 
            state1 = sb_data.tx_data[0].state 

            contract2 = sb_data.tx_data[1].contract 
            status2 = sb_data.tx_data[1].status 
            result2 = sb_data.tx_data[1].response 
            state2 = sb_data.tx_data[1].state 

            self.assertEqual(contract1, tx3)
            self.assertEqual(contract2, tx4)
            self.assertEqual(status1, 0)
            self.assertEqual(status2, 1)
            self.assertEqual(result1, 'tx3_succ')
            self.assertIsInstance(result2, ImportError)
            self.assertEqual(state1, '{}')
            self.assertEqual(state2, '')

        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx1_succ'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx2_succ'})
        tx3 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx3_succ'})
        tx4 = TransactionStub(self.author, 'module_func_bad', 'test_func', {'status': 'tx4_succ'})

        input_hash1 = 'A' * 64
        input_hash2 = 'B' * 64

        self.clients[0].execute_sb(input_hash1, [tx1, tx2], 0, _assert_handler1)
        self.clients[1].execute_sb(input_hash2, [tx3, tx4], 1, _assert_handler2)

        self.run_loop(2)






