from unittest import TestCase
from seneca.engine.util import make_n_tup
from seneca.interface.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException
from os.path import join
from tests.utils import captured_output
import redis, unittest, seneca, time
r = redis.StrictRedis(host='localhost', port=6379, db=0)

test_contracts_path = seneca.__path__[0] + '/test_contracts/'
CONTRACT_COUNT = 10000

class TestProtoTransfer(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface()
        self.rt = {'rt': make_n_tup({'sender': 'stu', 'author': 'stu'})}
        print('''
################################################################################
{}
################################################################################
        '''.format(self.id))
        self.mint_account()
        self.code_str = '''
from seneca.proto_contracts.kv_currency import transfer
transfer('ass', 1)
        '''
        self.print_balance()
        self.code_obj = self.si.get_code_obj(self.code_str)
        self.start = time.time()

    def tearDown(self):
        elapsed = time.time() - self.start
        print('Finished {} contracts in {}s!'.format(CONTRACT_COUNT, elapsed))
        print('Rate: {}tps'.format(CONTRACT_COUNT / elapsed))
        self.print_balance()

    def mint_account(self):
        self.si.execute_code_str("""
from seneca.proto_contracts.kv_currency import mint
mint('stu', {})
        """.format(CONTRACT_COUNT), self.rt)

    def print_balance(self):
        self.si.execute_code_str("""
from seneca.proto_contracts.kv_currency import balance_of
print('stu has a balance of: ' + str(balance_of('stu')))
print('ass has a balance of: ' + str(balance_of('ass')))
        """)

    def test_transfer_compile_on_the_go(self):
        for i in range(CONTRACT_COUNT):
            self.si.execute_code_str(self.code_str, self.rt)

    def test_transfer_precompiled(self):
        for i in range(CONTRACT_COUNT):
            self.si.run_code(self.code_obj)

if __name__ == '__main__':
    unittest.main()
