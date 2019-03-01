import unittest, seneca
from tests.utils import TestExecutor
from os.path import dirname

test_contracts_path = dirname(seneca.__path__[0]) + '/test_contracts'
AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'

class TestNoResetDB(TestExecutor):

    def test_1_no_reset_in_between(self):
        code_str = """
from seneca.libs.storage.datatypes import Hash

balances = Hash('balances')

@seed
def gv_mones():
    balances['birb'] = 1000000

@export
def ad_mones():
    balances['birb'] += 100
    
@export
def ls_mones():
    return balances['birb']
        """
        self.ex.publish_code_str('mones', AUTHOR, code_str)
        self.ex.execute_function('mones', 'ad_mones', 'mones', 0)
        self.ex.execute_function('mones', 'ad_mones', 'mones', 0)
        self.ex.execute_function('mones', 'ad_mones', 'mones', 0)
        self.ex.execute_function('mones', 'ad_mones', 'mones', 0)
        res = self.ex.execute_function('mones', 'ls_mones', 'mones', 0)
        self.assertEqual(res['output'], 1000400)

    def test_2_no_reset_in_between(self):
        self.ex.execute_function('mones', 'ad_mones', 'mones', 0)
        res = self.ex.execute_function('mones', 'ls_mones', 'mones', 0)
        self.assertEqual(res['output'], 1000500)


class TestResetDBWithStamps(TestExecutor):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        code_str = """
from seneca.libs.storage.datatypes import Hash
from seneca.contracts.currency import balance_of

monay = Hash('balances', default_value=0)

@export
def ad_mones():
    monay['birb'] += 100
    
@export
def ls_mones():
    return monay['birb']
    
            """
        cls.ex.publish_code_str('rad_mones', AUTHOR, code_str)
        cls.ex.currency = True

    def test_1_no_reset_in_between(self):
        TestResetDBWithStamps.balance = self.ex.execute_function('currency', 'balance_of', AUTHOR, 10000, kwargs={'wallet_id': "birb"})['output']
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        self.assertEqual(res['output'], 0)
        self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        self.assertEqual(res['output'], 400)
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, 10000, kwargs={'wallet_id': "birb"})
        self.assertEqual(res['output'], 400)

    def test_2_no_reset_in_between(self):
        self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        self.assertEqual(res['output'], 500)
        res = self.ex.execute_function('currency', 'balance_of', AUTHOR, 10000, kwargs={'wallet_id': "birb"})
        self.assertEqual(res['output'], 500)


if __name__ == '__main__':
    unittest.main()
