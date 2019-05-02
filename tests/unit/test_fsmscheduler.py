import unittest
import sys
import glob
import asyncio
import time
from contracting.execution.module import DatabaseFinder
from contracting.db.cr.cache import CRCache, Macros
from contracting.execution.executor import Executor
from contracting.db.driver import ContractDriver
from contracting.db.cr.transaction_bag import TransactionBag
from contracting.db.cr.client import FSMScheduler

driver = ContractDriver(db=0)

class PayloadStub():
    def __init__(self, sender):
        self.sender = sender

class TransactionStub():
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender)
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs

def completion_handler_stub(cache):
    pass

class TestMultiCRCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        num_sbb = 1
        self.master_db = driver
        executor = Executor(production=True)
        self.author = 'unittest'
        sys.meta_path.append(DatabaseFinder)
        driver.flush()

        # Add submission contract
        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        driver.set_contract(name='submission',
                            code=contract,
                            author='sys')
        driver.commit()

        # Use executor submit
        contracts = glob.glob('./test_sys_contracts/*.py')
        for contract in contracts:
            name = contract.split('/')[-1]
            name = name.split('.')[0]

            with open(contract) as f:
                code = f.read()

            executor.execute(sender=self.author, contract_name='submission', function_name='submit_contract', kwargs={'name': name, 'code': code})

        # Setup tx
        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx1_succ'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx2_succ'})
        tx3 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'tx3_succ'})
        tx4 = TransactionStub(self.author, 'module_func_bad', 'test_func', {'status': 'tx4_succ'})
        self.bags = [
            TransactionBag([tx1, tx2], 'A'*64, completion_handler_stub),
            TransactionBag([tx3, tx4], 'B'*64, completion_handler_stub)
        ]
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.num_caches = 2
        self.caches = []
        self.scheduler = FSMScheduler(self.loop, sbb_idx=0, num_sbb=num_sbb)
        for cache_idx in range(self.num_caches):
            self.caches.append(CRCache(idx=cache_idx+1, master_db=self.master_db, sbb_idx=0, num_sbb=num_sbb,
                               executor=executor, scheduler=self.scheduler))

    @classmethod
    def tearDownClass(self):
        self.master_db.flush()
        for i in range(self.num_caches):
            self.caches[i].db.flush()
            self.caches[i].executor.sandbox.terminate()
        sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def run_loop(self, period=1):
        async def run():
            await asyncio.sleep(period)

        self.loop.run_until_complete(run())

    def test_0_init(self):
        for i in range(self.num_caches):
            self.assertTrue(self.caches[i] in self.scheduler.available_caches)
        self.assertTrue(len(self.scheduler.pending_caches) == 0)

    def test_1_execute_bag(self):
        for i in range(self.num_caches):
            self.scheduler.execute_bag(self.bags[i])
            self.run_loop()
            if i == 0:
                self.assertEqual(self.caches[i].state, 'READY_TO_MERGE')
            else:
                self.assertEqual(self.caches[i].state, 'EXECUTED')

    def test_2_execution_order(self):
        for i in range(self.num_caches):
            self.scheduler.update_master_db()
            self.run_loop(2)
            self.assertEqual(self.caches[i].state, 'CLEAN')
            self.assertTrue(self.caches[i] in self.scheduler.available_caches)
            self.assertTrue(self.caches[i] not in self.scheduler.pending_caches)
            if i < self.num_caches-1:
                self.assertEqual(self.caches[i+1].state, 'READY_TO_MERGE')
