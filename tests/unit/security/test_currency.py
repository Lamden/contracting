from tests.utils import TestExecutor
from seneca.constants.config import get_redis_port, get_redis_password
import redis, unittest, seneca
from os.path import dirname

test_contracts_path = dirname(seneca.__path__[0]) + '/test_contracts'
AUTHOR = '__lamden_io__'

class TestCurrency(TestExecutor):

    def test_unauthorized_transfer(self):
        self.ex.execute_function('currency', 'mint', AUTHOR, 0, kwargs={'to':'birb', 'amount':10000000})
        code_str = """
from seneca.libs.datatypes import hmap
from seneca.contracts.currency import transfer, balance_of

@export
def rm_mones():
    transfer('blackhole', 100) # Not allowed to write a contract that

                    """
        self.ex.publish_code_str('bad_mones', AUTHOR, code_str)
        with self.assertRaises(AssertionError) as context:
            self.ex.execute_function('bad_mones', 'rm_mones', 'birb', 10000)

if __name__ == '__main__':
    unittest.main()
