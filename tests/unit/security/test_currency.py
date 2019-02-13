from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.constants.config import get_redis_port, get_redis_password
import redis, unittest, seneca
from os.path import dirname

test_contracts_path = dirname(seneca.__path__[0]) + '/test_contracts'
AUTHOR = 'anonymoose'

class TestCurrency(TestCase):

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
from seneca.contracts.currency import transfer, balance_of

@export
def rm_mones():
    transfer('blackhole', 100) # Not allowed to write a contract that

@export
def ls_mones():
    return balance_of('birb')
            """
        cls.si.publish_code_str('bad_mones', AUTHOR, code_str)
        cls.si.bypass_currency = False

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    def test_unauthorized_transfer(self):
        with self.assertRaises(AssertionError) as context:
            self.si.execute_function('seneca.contracts.bad_mones.rm_mones', 'birb', 10000)

if __name__ == '__main__':
    unittest.main()
