import unittest
import sys
import glob
import time
from contracting.execution.module import DatabaseFinder
from contracting.db.cr.cache import CRCache, Macros
from contracting.execution.executor import Executor
from contracting.db.driver import ContractDriver
from contracting.db.cr.transaction_bag import TransactionBag

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


#unittest.TestLoader.sortTestMethodsUsing = None


class TestSingleCRCache(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.driver = ContractDriver(db=0)
        num_sbb = 1
        self.master_db = self.driver
        executor = Executor(production=True, metering=False)
        self.author = 'unittest'
        sys.meta_path.append(DatabaseFinder)
        self.driver.flush()

        # Add submission contract
        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.driver.set_contract(name='submission',
                            code=contract,
                            author='sys')

        self.driver.commit()

        with open('./test_sys_contracts/module_func.py') as f:
            code = f.read()

        executor.execute(sender=self.author, contract_name='submission', function_name='submit_contract', kwargs={'name': 'module_func', 'code': code})

        # Setup tx
        tx1 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'Working'})
        tx2 = TransactionStub(self.author, 'module_func', 'test_func', {'status': 'AlsoWorking'})
        tx3 = TransactionStub(self.author, 'module_func', 'test_keymod', {'deduct': 10})
        input_hash = 'A'*64
        sbb_idx = 0
        # self.cache_mgr = SchedulerStub()
        self.bag = TransactionBag([tx1, tx2, tx3], input_hash, 0, lambda y: y)
        self.cache = CRCache(idx=1, master_db=self.master_db, sbb_idx=sbb_idx,
                             num_sbb=num_sbb, executor=executor)

    @classmethod
    def tearDownClass(self):
        self.cache.db.flush()
        self.master_db.flush()
        self.cache.executor.sandbox.terminate()
        #del self.cache
        #sys.meta_path.remove(DatabaseFinder)
        self.driver.flush()

    def test_1_execute(self):
        self.cache.execute_bag(self.bag)

        results = self.cache.get_results()
        print(results)
        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[0][1], 'Working')
        self.assertEqual(results[1][0], 0)
        self.assertEqual(results[1][1], 'AlsoWorking')
        self.assertEqual(results[2][0], 0)
        self.assertEqual(results[2][1], 90)

        self.assertEqual(0, self.cache._get_macro_value(Macros.CONFLICT_RESOLUTION))
        self.assertEqual(0, self.cache._get_macro_value(Macros.RESET))

    def test_2_cr(self):
        self.cache.cr_event()
        self.assertEqual(1, self.cache._get_macro_value(Macros.CONFLICT_RESOLUTION))

        # Test if the cache db has the updated value and master is still holding the correct old value
        self.assertEqual(int(self.cache.db.get_direct('module_func.balances:test')), 90)
        self.assertEqual(int(self.cache.master_db.get_direct('module_func.balances:test')), 100)
        # Run the same test without bypassing the cache
        self.assertEqual(int(self.cache.db.get('module_func.balances:test')), 90)
        self.assertEqual(int(self.cache.master_db.get('module_func.balances:test')), 100)

    def test_3_merged(self):
        self.cache.merge_to_master()

        self.assertEqual(int(self.cache.master_db.get_direct('module_func.balances:test')), 90)
        self.assertEqual(int(self.cache.master_db.get('module_func.balances:test')), 90)

    def test_4_clean(self):
        self.cache.reset_dbs()
        self.cache.mark_clean()
        self.assertEqual(self.cache.is_reset(), False)



# if __name__ == "__main__":
#     unittest.main()
