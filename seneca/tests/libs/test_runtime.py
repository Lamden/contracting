from unittest import TestCase
from seneca.libs.runtime import *
from seneca.engine.util import make_n_tup


class TestRuntime(TestCase):
    def setUp(self):
        self.x = make_n_tup(make_exports([('test_author', 'test_contract_addr')]))

    def test_sender(self):
        self.assertEqual(self.x.sender, 'test_author')

    def test_this_contract_author(self):
        self.assertEqual(self.x.this_contract.author, 'test_author')

    def test_this_contract_address(self):
        self.assertEqual(self.x.this_contract.address, 'test_contract_addr')

    def test_call_stack(self):
        expected = [{'author': 'test_author', 'address': 'test_contract_addr', '_call_stack_index': 0}]

        self.assertListEqual(expected, eval(str(self.x.call_stack)))

    def test_upstream_does_not_exist(self):
        try:
            self.x.this_contract.upstream()
            self.assertTrue(1 == 2)
        except Exception as e:
            self.assertTrue(1 == 1)

    def test_sender_two_contracts(self):
        x = make_n_tup(make_exports([
            ('caller_author', 'caller_contract'),
            ('lib_author', 'lib_contract')
            ]))

        self.assertEqual(x.sender, 'caller_author')

    def test_lib_author_two_contracts(self):
        x = make_n_tup(make_exports([
            ('caller_author', 'caller_contract'),
            ('lib_author', 'lib_contract')
        ]))

        self.assertEqual(x.this_contract.author, 'lib_author')

    def test_upstream_author_two_contracts(self):
        x = make_n_tup(make_exports([
            ('caller_author', 'caller_contract'),
            ('lib_author', 'lib_contract')
        ]))

        self.assertEqual(x.this_contract.upstream().author, 'caller_author')

    def test_upstream_address_two_contracts(self):
        x = make_n_tup(make_exports([
            ('caller_author', 'caller_contract'),
            ('lib_author', 'lib_contract')
        ]))

        self.assertEqual(x.this_contract.upstream().address, 'caller_contract')
