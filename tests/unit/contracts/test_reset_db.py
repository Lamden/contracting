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
        cls.balances = cls.ex.get_resource('currency', 'balances')
        cls.seed_amount = cls.ex.get_resource('currency', 'seed_amount')
        cls.stamps_used = 0

    def test_1_no_reset_in_between(self):
        TestResetDBWithStamps.balance = self.balances['birb']
        stamps_used = 0
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        self.assertEqual(res['output'], 0)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        self.assertEqual(res['output'], 400)
        self.assertEqual(self.balances[AUTHOR]+stamps_used, self.seed_amount)
        TestResetDBWithStamps.stamps_used += stamps_used

    def test_2_no_reset_in_between(self):
        stamps_used = 0
        res = self.ex.execute_function('rad_mones', 'ad_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        res = self.ex.execute_function('rad_mones', 'ls_mones', AUTHOR, 10000)
        stamps_used += res['stamps_used']
        self.assertEqual(res['output'], 500)
        TestResetDBWithStamps.stamps_used += stamps_used
        self.assertEqual(self.balances[AUTHOR]+TestResetDBWithStamps.stamps_used, self.seed_amount)


if __name__ == '__main__':
    unittest.main()
