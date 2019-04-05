import unittest
from seneca.libs.storage.datatypes import Hash
from seneca.libs.storage.table import Property
from tests.utils import TestDataTypes


class TestHash(TestDataTypes):

    def test_hash_minimum(self):
        balances = Hash('balances')
        balances['hr'] = Hash('hr')
        self.assertEqual(repr(balances['hr']), 'Hash:test_hash_minimum:balances:hr')

    def test_hash_simple(self):
        balances = Hash('balances')
        balances['hr']['employees']['stu'] = 100
        self.assertEqual(balances['hr']['employees']['stu'], 100)

    # TODO: Pointers currently not supported by CR
    # def test_hash_nested(self):
    #     balances = Hash('balances')
    #     hooter = Hash('hoot')
    #     hooter['res'] = 1234
    #     balances['hr'] = Hash('hr')
    #     balances['hr']['hey'] = hooter
    #     self.assertEqual(balances['hr']['hey']['res'], 1234)


if __name__ == '__main__':
    unittest.main()
