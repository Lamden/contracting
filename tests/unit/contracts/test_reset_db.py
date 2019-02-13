from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.constants.config import get_redis_port, get_redis_password
import redis, unittest, seneca
from os.path import dirname

test_contracts_path = dirname(seneca.__path__[0]) + '/test_contracts'
AUTHOR = 'anonymoose'

class TestResetDB(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.si = SenecaInterface(False, port=get_redis_port(), password=get_redis_password())
        cls.si.bypass_currency = True
        cls.si.r.flushall()

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    def test_1_no_reset_in_between(self):
        code_str = """
from seneca.libs.datatypes import hmap

balances = hmap('balances', str, int)

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
        self.si.publish_code_str('mones', AUTHOR, code_str)
        self.si.execute_function('seneca.contracts.mones.ad_mones', 'mones', 0)
        self.si.execute_function('seneca.contracts.mones.ad_mones', 'mones', 0)
        self.si.execute_function('seneca.contracts.mones.ad_mones', 'mones', 0)
        self.si.execute_function('seneca.contracts.mones.ad_mones', 'mones', 0)
        res = self.si.execute_function('seneca.contracts.mones.ls_mones', 'mones', 0)
        self.assertEqual(res['output'], 1000400)

    def test_2_no_reset_in_between(self):
        self.si.execute_function('seneca.contracts.mones.ad_mones', 'mones', 0)
        res = self.si.execute_function('seneca.contracts.mones.ls_mones', 'mones', 0)
        self.assertEqual(res['output'], 1000500)


class TestResetDBWithStamps(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.si = SenecaInterface(False, port=get_redis_port(), password=get_redis_password())
        cls.si.r.flushall()
        cls.si.bypass_currency = True
        with open('{}/currency.sen.py'.format(test_contracts_path)) as f:
            cls.si.publish_code_str('currency', AUTHOR, f.read())
        cls.si.execute_function('seneca.contracts.currency.mint', AUTHOR, 0, to='birb', amount=10000000)
        code_str = """
from seneca.libs.datatypes import hmap
from seneca.contracts.currency import balance_of

monay = hmap('balances', str, int)

@export
def ad_mones():
    monay[rt['origin']] += 100
    
@export
def ls_mones():
    return monay[rt['origin']]
    
            """
        cls.si.publish_code_str('rad_mones', AUTHOR, code_str)
        cls.si.bypass_currency = False


    def setUp(self):
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    def test_1_no_reset_in_between(self):
        TestResetDBWithStamps.balance = self.si.execute_function('seneca.contracts.currency.balance_of', 'birb', 10000, wallet_id="birb")['output']
        res = self.si.execute_function('seneca.contracts.rad_mones.ls_mones', 'birb', 10000)
        self.assertEqual(res['output'], 0)
        self.si.execute_function('seneca.contracts.rad_mones.ad_mones', 'birb', 10000)
        self.si.execute_function('seneca.contracts.rad_mones.ad_mones', 'birb', 10000)
        self.si.execute_function('seneca.contracts.rad_mones.ad_mones', 'birb', 10000)
        self.si.execute_function('seneca.contracts.rad_mones.ad_mones', 'birb', 10000)
        res = self.si.execute_function('seneca.contracts.rad_mones.ls_mones', 'birb', 10000)
        self.assertEqual(res['output'], 400)
        res = self.si.execute_function('seneca.contracts.currency.balance_of', 'birb', 10000, wallet_id="birb")
        self.assertEqual(res['output'], TestResetDBWithStamps.balance - 70000)

    def test_2_no_reset_in_between(self):
        self.si.execute_function('seneca.contracts.rad_mones.ad_mones', 'birb', 10000)
        res = self.si.execute_function('seneca.contracts.rad_mones.ls_mones', 'birb', 10000)
        self.assertEqual(res['output'], 500)
        res = self.si.execute_function('seneca.contracts.currency.balance_of', 'birb', 10000, wallet_id="birb")
        self.assertEqual(res['output'], TestResetDBWithStamps.balance - 100000)


class TestResetDB(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.si = SenecaInterface(False, port=get_redis_port(), password=get_redis_password())
        cls.si.bypass_currency = True

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    @property
    def code_str(self):
        return """
from seneca.libs.datatypes import hmap
from seneca.contracts.currency import balance_of

monay = hmap('balances', str, int)

@export
def ad_mones():
    monay[rt['origin']] += 100

@export
def ls_mones():
    return monay[rt['origin']]
        """

    def test_1_republish_in_between_runs(self):
        self.si.r.flushall()
        with open('{}/currency.sen.py'.format(test_contracts_path)) as f:
            self.si.publish_code_str('currency', AUTHOR, f.read())
        self.si.execute_function('seneca.contracts.currency.mint', AUTHOR, 0, to='birb', amount=10000000)
        self.si.publish_code_str('rad_name', AUTHOR, self.code_str)


    def test_2_republish_in_between_runs(self):
        self.si.r.flushall()
        with self.assertRaises(Exception) as context:
            self.si.execute_function('seneca.contracts.rad_name.ad_mones', 'birb', 10000)

if __name__ == '__main__':
    unittest.main()
