from unittest import TestCase
from contracting.stdlib.bridge.hashing import sha256, sha3


class TestHashing(TestCase):
    def test_sha3(self):
        secret = '1a54390942257a70bb843c1bd94eb996'
        _hash = '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7'

        self.assertEqual(_hash, sha3(secret))

    def test_sha256(self):
        secret = '842b65a7d48e3a3c3f0e9d37eaced0b2'
        _hash = 'eaf48a02d3a4bb3aeb0ecb337f6efb026ee0bbc460652510cff929de78935514'

        self.assertEqual(_hash, sha256(secret))