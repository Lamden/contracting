from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException
from seneca.engine.book_keeper import BookKeeper
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password
from os.path import join
from tests.utils import captured_output
from multiprocessing import Pool, Process
import redis, unittest, seneca, time
import multiprocessing
from seneca.libs.logger import get_logger

r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
test_contracts_path = seneca.__path__[0] + '/test_contracts/'
CONTRACT_COUNT = 10000
users = ['stu', 'dav', 'fal', 'rag']
TOTAL_COUNT = len(users) * CONTRACT_COUNT

class TestMultiProc(TestCase):

    def setUp(self):
        r.flushdb()
        self.si = SenecaInterface(False)
        print('''
################################################################################
{}
################################################################################
        '''.format(self.id))
        for user in users:
            self.mint_account(user)
        self.code_str = '''
from test_contracts.kv_currency import transfer
transfer('tej', 1)
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
        """.format(user, CONTRACT_COUNT), {'rt': {'sender': user, 'author': user, 'contract': 'test'}})

    def print_balance(self):
        self.si.execute_code_str("""
from test_contracts.kv_currency import balance_of
print('stu has a balance of: ' + str(balance_of('stu')))
print('dav has a balance of: ' + str(balance_of('dav')))
print('fal has a balance of: ' + str(balance_of('fal')))
print('rag has a balance of: ' + str(balance_of('rag')))
print('tej has a balance of: ' + str(balance_of('tej')))
        """, {'rt': {'sender': 'stu', 'author': 'stu'}})

    def test_transfer_template(self):
        def run_code_obj(user):
            si = SenecaInterface(False)
            SenecaInterpreter.setup(False)
            for i in range(CONTRACT_COUNT):
                si.execute_function('test_contracts.kv_currency.transfer',
                    user, 10000, 'tej', 1)
        processes = [
            Process(target=run_code_obj, args=(user,)) \
            for user in users
        ]
        [p.start() for p in processes]
        [p.join() for p in processes]

if __name__ == '__main__':
    unittest.main()
