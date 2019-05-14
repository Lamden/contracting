import unittest
import sys
import glob
import time
from contracting.execution.module import DatabaseFinder
from contracting.db.cr.cache import CRCache, Macros
from contracting.execution.executor import Executor
from contracting.db.driver import ContractDriver
from contracting.db.cr.transaction_bag import TransactionBag

class PayloadStub():
    def __init__(self, sender):
        self.sender = sender

class TransactionStub():
    def __init__(self, sender, contract_name, func_name, kwargs):
        self.payload = PayloadStub(sender)
        self.contract_name = contract_name
        self.func_name = func_name
        self.kwargs = kwargs

class SchedulerStub():
    def __init__(self):
        self.polls = {}
        self.top_of_stack = False

    def add_poll(self, cache, fn, endstate):
        if cache not in self.polls.keys():
            self.polls[cache] = {}
        self.polls[cache][fn] = endstate

    def execute_poll(self, cache, fn):
        fn()
        return cache.state == self.polls[cache][fn]

    def mark_top_of_stack(self):
        self.top_of_stack = True

    def check_top_of_stack(self, cache):
        return self.top_of_stack

    def mark_clean(self, cache):
        pass



driver = ContractDriver(db=0)
#unittest.TestLoader.sortTestMethodsUsing = None


class TestSingleCRCache(unittest.TestCase):
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

        with open('./test_sys_contracts/module_func.py') as f:
            code = f.read()

        executor.execute(sender=self.author, contract_name='submission', function_name='submit_contract', kwargs={'name': 'module_func', 'code': code})

        # Setup tx
        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'Working'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'AlsoWorking'})
        input_hash = 'A'*64
        sbb_idx = 0
        self.scheduler = SchedulerStub()
        self.bag = TransactionBag([tx1, tx2], input_hash, lambda y: y)
        self.cache = CRCache(idx=1, master_db=self.master_db, sbb_idx=sbb_idx,
                             num_sbb=num_sbb, executor=executor, scheduler=self.scheduler)

    @classmethod
    def tearDownClass(self):
        self.cache.db.flush()
        self.master_db.flush()
        self.cache.executor.sandbox.terminate()
        #del self.cache
        #sys.meta_path.remove(DatabaseFinder)
        driver.flush()

    def test_0_set_bag(self):
        self.cache.set_bag(self.bag)

        self.assertEqual(self.cache.state, 'BAG_SET')

    def test_1_execute(self):
        self.cache.execute()
        self.assertEqual(self.cache.state, 'EXECUTED')

        results = self.cache.get_results()
        print(results)
        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[0][1], 'Working')
        self.assertEqual(results[1][0], 0)
        self.assertEqual(results[1][1], 'AlsoWorking')

        self.assertEqual(0, self.cache._check_macro_key(Macros.CONFLICT_RESOLUTION))
        self.assertEqual(0, self.cache._check_macro_key(Macros.RESET))
        self.assertEqual(1, self.cache._check_macro_key(Macros.EXECUTION))

    def test_2_cr(self):
        res = self.scheduler.execute_poll(self.cache, self.cache.sync_execution)
        self.assertEqual(self.cache.state, 'EXECUTED')
        self.assertEqual(res, False)

        self.scheduler.mark_top_of_stack()
        res = self.scheduler.execute_poll(self.cache, self.cache.sync_execution)
        self.assertEqual(self.cache.state, 'COMMITTED')
        self.assertEqual(res, True)

    def test_3_merge_ready(self):
        res = self.scheduler.execute_poll(self.cache, self.cache.sync_merge_ready)
        self.assertEqual(self.cache.state, 'READY_TO_MERGE')
        self.assertEqual(res, True)

    def test_4_merged(self):
        self.cache.merge()
        self.assertEqual(self.cache.state, 'RESET')

    def test_5_clean(self):
        res = self.scheduler.execute_poll(self.cache, self.cache.sync_reset)
        self.assertEqual(self.cache.state, 'CLEAN')
        self.assertEqual(res, True)



# if __name__ == "__main__":
#     unittest.main()
