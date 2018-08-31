from unittest import TestCase
from seneca.libs.crypto import hashing
import hashlib


class TestHashing(TestCase):
    def test_hashes(self):
        payload = b'testing this'
        algos = hashing.supported_hashing_functions

        for algo in algos:
            m = hashlib.new(algo)
            m.update(payload)

            m2 = hashing.exports[algo](payload)

            self.assertEqual(m.digest(), m2)
