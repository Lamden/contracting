from unittest import TestCase
import redis, unittest
from seneca.constants.config import MASTER_DB, REDIS_PORT
from seneca.engine.interpret.parser import Parser
from seneca.engine.interpret.driver import Driver


class Executor:
    def __init__(self):
        self.driver = Driver(host='localhost', port=REDIS_PORT, db=MASTER_DB)
        self.driver.flushall()
        Parser.executor = self
        Parser.parser_scope = {
            'rt': {
                'contract': 'sample',
                'sender': 'falcon',
                'author': '__lamden_io__'
            }
        }


_ex = Executor()
from seneca.libs.storage.datatypes import Hash, Set, Array, ZSet, HyperLogLog, BitField, BloomFilter


class TestDataTypes(TestCase):

    def setUp(self):
        self.contract_id = self.id().split('.')[-1]
        self.ex = _ex
        Parser.parser_scope['rt']['contract'] = self.contract_id
        print('#'*128)
        print('\t', self.contract_id)
        print('#'*128)

    # def test_hash(self):
    #     balances = Hash('balances')
    #     balances['hr'] = Hash('hr')
    #     balances['hr']['sucks'] = 1
    #     print(balances['hr']['sucks'])
    #     # self.assertEqual(repr(balances['hr']), 'Map:{}:balances:hr'.format(self.contract_id))

    def test_set(self):
        s1 = Set('s1')
        s1.add(*range(5))
        print(s1)


if __name__ == '__main__':
    unittest.main()
