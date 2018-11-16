from unittest import TestCase
from seneca.libs.datatypes2 import *


class TestDatatypes(TestCase):
    def setUp(self):
        Registry.flush()

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
        self.assertEqual(Registry.mapping, {})
        self.assertEqual(Registry.count, 0)

        Int(use_local=True)
        self.assertEqual(Registry.count, 1)
        Registry.flush()

        self.assertEqual(Registry.mapping, {})
        self.assertEqual(Registry.count, 0)

    def test_registry_get_key(self):
        i = Int(use_local=True)
        self.assertEqual(i.key, Registry.get_key(i))

    def test_int(self):
        i = Int(use_local=True)
        i.set(5)
        self.assertEqual(i.get(), 5)
        i.set(6)
        self.assertEqual(i.get(), 6)
        self.assertEqual(i.get(), 6)

    def test_str(self):
        s = Str(use_local=True)
        s.set('stu')
        self.assertEqual(s.get(), 'stu')
        s.set('123')
        self.assertEqual(s.get(), '123')

    def test_bool(self):
        b = Bool(use_local=True)
        b.set(True)
        self.assertTrue(b.get())
        b.set(False)
        self.assertFalse(b.get())

    def test_bytes(self):
        b = Bytes(use_local=True)
        b.set(b'howdy')
        self.assertEqual(b.get(), b'howdy')
        b.set(b'pardner')
        self.assertEqual(b.get(), b'pardner')