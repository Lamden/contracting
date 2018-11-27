from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, ReadOnlyException
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password
from os.path import join
from tests.utils import captured_output
import redis, unittest, seneca, time
r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())

test_contracts_path = seneca.__path__[0] + '/../test_contracts/'
CONTRACT_COUNT = 10000

class TestPublishTransfer(TestCase):

    def setUp(self):
        r.flushdb()
        SenecaInterpreter.setup()
        SenecaInterpreter.concurrent_mode = False
        self.si = SenecaInterface(False)
        self.author = 'stu'
        self.sender = 'stu'
        self.rt = {'rt': {'sender': self.sender, 'author': self.author, 'contract': 'test'}}
        print('''
################################################################################
{}
################################################################################
        '''.format(self.id))
        self.publish_contract()
        self.mint_account()
        self.code_str = '''
from seneca.contracts.kv_currency import transfer
transfer('ass', 1)
        '''
        self.print_balance()
        self.code_obj = self.si.compile_code(self.code_str)
        self.start = time.time()

    def tearDown(self):
        elapsed = time.time() - self.start
        print('Finished {} contracts in {}s!'.format(CONTRACT_COUNT, elapsed))
        print('Rate: {}tps'.format(CONTRACT_COUNT / elapsed))
        self.print_balance()

    def publish_contract(self):
        with open(join(test_contracts_path, 'kv_currency.sen.py')) as f:
            self.si.publish_code_str('kv_currency', 'falcon', f.read(), keep_original=True)

    def mint_account(self):
        self.si.execute_code_str("""
from seneca.contracts.kv_currency import mint
mint('stu', {})
        """.format(CONTRACT_COUNT), self.rt)

    def print_balance(self):
        self.si.execute_code_str("""
from seneca.contracts.kv_currency import balance_of
print('stu has a balance of: ' + str(balance_of('stu')))
print('ass has a balance of: ' + str(balance_of('ass')))
        """)

    def test_transfer_template_with_metering(self):
        for i in range(CONTRACT_COUNT):
            self.si.execute_function('test_contracts.kv_currency.transfer',
                self.sender, 100000, 'ass', amount=1)

if __name__ == '__main__':
    unittest.main()
