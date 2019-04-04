from unittest import TestCase
from seneca.loaders.loader import *


class TestDatabase(TestCase):
    def setUp(self):
        self.d = Database(host='localhost', port=6379, db=10)
        self.d.flush()

    def tearDown(self):
        self.d.flush()

    def test_init(self):
        self.assertEqual(self.d.delimiter, ':', 'Delimiter default not :.')
        self.assertEqual(self.d.code_key, 'code', 'Code Key default not "code"')

    def test_dynamic_init(self):
        d = Database(host='localhost', port=6379, delimiter='*', db=9, code_key='jam')

        self.assertEqual(d.delimiter, '*', 'self.delimiter is not being set')
        self.assertEqual(d.code_key, 'jam', 'self.code_key is not being set')

    def test_push_and_get_contract(self):
        code = 'a = 123'
        name = 'test'

        self.d.push_contract(name, code)
        _code = self.d.get_contract(name)

        self.assertEqual(code, _code, 'Pushing and getting contracts is not working.')

    def test_flush(self):
        code = 'a = 123'
        name = 'test'

        self.d.push_contract(name, code)
        self.d.flush()

        with self.assertRaises(Exception):
            self.d.get_contract(name)
