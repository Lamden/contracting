from unittest import TestCase
from seneca.libs.datatypes2 import *


class TestDatatypes(TestCase):
    def test_registry_sanity(self):
        o = Int(use_local=True)

        test_sha3 = hashlib.sha3_256()
        test_sha3.update(b'')
        test_hash = test_sha3.digest()

        test_sha3 = hashlib.sha3_256()
        test_sha3.update(test_hash)
        test_sha3.update(b'\x00')

        self.assertEqual(Registry.get_key(o), test_sha3.digest())

    def test_registry_flush(self):
        o = Int(use_local=True)
        Registry.flush()

        self.assertEqual(Registry.mapping, {})
        self.assertEqual(Registry.count, 0)

