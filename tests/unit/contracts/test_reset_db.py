from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.constants.config import get_redis_port, get_redis_password
import redis, unittest, seneca

test_contracts_path = seneca.__path__[0] + '/test_contracts/'
SENDER = 'anonymoose'

class TestResetDB(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.si = SenecaInterface(False)
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
        self.si.publish_code_str('mones', SENDER, code_str)
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

if __name__ == '__main__':
    unittest.main()
