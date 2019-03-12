from tests.utils import TestExecutor
import ledis, unittest, seneca
from os.path import dirname

test_contracts_path = dirname(seneca.__path__[0]) + '/test_contracts'
AUTHOR = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'

class TestCurrency(TestExecutor):

    def test_unauthorized_transfer(self):
        self.ex.execute_function('currency', 'transfer', AUTHOR, 0, kwargs={'to': 'birb', 'amount': 100000})
        code_str = """
from seneca.contracts.currency import transfer

@export
def rm_mones():
    transfer('blackhole', 100) # Not allowed to write a contract that

                    """
        self.ex.publish_code_str('bad_mones', AUTHOR, code_str)
        with self.assertRaises(AssertionError) as context:
            self.ex.execute_function('bad_mones', 'rm_mones', 'birb', 10000)

if __name__ == '__main__':
    unittest.main()
