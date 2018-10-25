from unittest import TestCase
from seneca.engine.util import make_n_tup
from seneca.interface.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException
from os.path import join
from tests.utils import captured_output
from multiprocessing import Pool, Process
import redis, unittest, seneca, time
import multiprocessing

r = redis.StrictRedis(host='localhost', port=6379, db=0)
test_contracts_path = seneca.__path__[0] + '/test_contracts/'
CONTRACT_COUNT = 10000
users = ['stu', 'dav', 'fal', 'rag']
TOTAL_COUNT = len(users) * CONTRACT_COUNT

class TestMultiProc(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface()
        print('''
################################################################################
{}
################################################################################
        '''.format(self.id))
        for user in users:
            self.mint_account(user)
        self.code_str = '''
from test_contracts.kv_currency import transfer
transfer('taj', 1)
        '''
        self.print_balance()
        self.code_obj = self.si.compile_code(self.code_str)
        self.start = time.time()

    def tearDown(self):
        elapsed = time.time() - self.start
        print('Finished {} contracts in {}s!'.format(TOTAL_COUNT, elapsed))
        print('Rate: {}tps'.format(TOTAL_COUNT / elapsed))
        self.print_balance()

    def mint_account(self, user):
        self.si.execute_code_str("""
from test_contracts.kv_currency import mint
mint('{}', {})
        """.format(user, CONTRACT_COUNT), {'rt': make_n_tup({'sender': user, 'author': user})})

    def print_balance(self):
        self.si.execute_code_str("""
from test_contracts.kv_currency import balance_of
print('stu has a balance of: ' + str(balance_of('stu')))
print('dav has a balance of: ' + str(balance_of('dav')))
print('fal has a balance of: ' + str(balance_of('fal')))
print('rag has a balance of: ' + str(balance_of('rag')))
print('taj has a balance of: ' + str(balance_of('taj')))
        """, {'rt': make_n_tup({'sender': 'stu', 'author': 'stu'})})

    def test_transfer_compile_on_the_go(self):
        def run_code_str(user):
            si = SenecaInterface()
            code_str = '''
from test_contracts.kv_currency import transfer
transfer('taj', 1)
            '''
            for i in range(CONTRACT_COUNT):
                si.execute_code_str(code_str, {'rt': make_n_tup({'sender': user, 'author': user})})
        processes = [
            Process(target=run_code_str, args=(user,)) \
            for user in users
        ]
        [p.start() for p in processes]
        [p.join() for p in processes]

    def test_transfer_precompiled(self):
        def run_code_obj(user):
            si = SenecaInterface()
            code_str = '''
from test_contracts.kv_currency import transfer
transfer('taj', 1)
            '''
            code_obj = si.compile_code(code_str)
            for i in range(CONTRACT_COUNT):
                si.run_code(code_obj, {'rt': make_n_tup({'sender': user, 'author': user})})
        processes = [
            Process(target=run_code_obj, args=(user,)) \
            for user in users
        ]
        [p.start() for p in processes]
        [p.join() for p in processes]

if __name__ == '__main__':
    unittest.main()
