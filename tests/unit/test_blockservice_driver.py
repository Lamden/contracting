from unittest import TestCase
from contracting.db.driver import BlockserviceDriver
from contracting.db.encoder import encode, MONGO_MAX_INT
from contracting.stdlib.bridge.time import Datetime, Timedelta
from contracting.stdlib.bridge.decimal import ContractingDecimal
import random

SAMPLE_STRING = 'beef'
SAMPLE_INT = 123
SAMPLE_BIGINT = MONGO_MAX_INT
SAMPLE_DATETIME = Datetime(year=2022, month=1, day=1)
SAMPLE_CONTRACTING_DECIMAL = ContractingDecimal(123.123)
SAMPLE_TIMEDELTA = Timedelta(weeks=1, days=1, hours=1)
SAMPLE_BYTES = bytes(b'0xbeef')
SAMPLE_DICT = {
    'a': SAMPLE_INT,
    'b': False,
    'c': SAMPLE_BIGINT,
    'd': SAMPLE_DATETIME,
    'e': SAMPLE_CONTRACTING_DECIMAL,
    'f': SAMPLE_TIMEDELTA,
    'g': SAMPLE_BYTES,
    'h': SAMPLE_STRING,
    'x': None
}

TEST_DATA = [
    SAMPLE_STRING, SAMPLE_INT, SAMPLE_BIGINT, SAMPLE_DATETIME,
    SAMPLE_CONTRACTING_DECIMAL, SAMPLE_TIMEDELTA, SAMPLE_BYTES, SAMPLE_DICT
]

class TestBlockserviceDriver(TestCase):
 
    def setUp(self):
        self.d = BlockserviceDriver()
        self.d.db.drop()

    def dbset(self, key, value):
        v = encode(value)
        self.d.db.update_one({'rawKey': key}, {'$set': {'value': v}}, upsert=True, )

    def test_get(self):
        for v in TEST_DATA:
            self.dbset('b', v)

            b = self.d.get('b')

            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)

    def test_iter(self):

        prefix_1_keys = [
            'b77aa343e339bed781c7c2be1267cd597',
            'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
            'b93dbb37d993846d70b8a92779cbfbfe9',
            'be1a2783019de6ea7ef169cc55e48a3ae',
            'b1fe8db32b9185d628f4c346f0455023e',
            'bef918f83b6a0d1e4f980013342807cf8',
            'b004cb9235acb5f689d20904692bc026e',
            'b869ff9519d67354816af90867f4a5425',
            'bcd8e9100dcb601f65e849c147e3e972e',
            'b0111919a698f9816862b4ae662a6ed06',
        ]

        prefix_2_keys = [
            'x37fbab0bd2e60563c79469e5be41e515',
            'x30c6eb2ad176773b5ce6d590d2472dfe',
            'x3d4fc9480f0a07b28aa7646d5066b54d',
            'x387c3d4ab7f0c1c6ef549198fc14b525',
            'x5c74dc83e132e435e8512599e1075bc0',
            'x1472425d0d9bb5ff511e132896d54b13',
            'x2cedb5c52163c22a0b5f179001959dd2',
            'x6223f65e553280cd25cadeac6657555c',
            'xeae18af37c223dde92a71fef55e64afe',
            'xb8810784ffb360cd3ffc57b1d088e537',
        ]

        keys = prefix_1_keys + prefix_2_keys
        random.shuffle(keys)

        for k in keys:
            self.dbset(k, k)

        p1 = []

        for k in self.d.iter(prefix='b'):
            p1.append(k)

        prefix_1_keys.sort()
        p1.sort()

        self.assertListEqual(prefix_1_keys, p1)

        p2 = []

        for k in self.d.iter(prefix='x'):
            p2.append(k)

        prefix_2_keys.sort()
        p2.sort()

        self.assertListEqual(prefix_2_keys, p2)
    
    def test_keys_returns_all_keys(self):
        prefix_1_keys = [
            'b77aa343e339bed781c7c2be1267cd597',
            'bc22ede6e6fb4046d78bf2f9d1f8afdb6',
            'b93dbb37d993846d70b8a92779cbfbfe9',
            'be1a2783019de6ea7ef169cc55e48a3ae',
            'b1fe8db32b9185d628f4c346f0455023e',
            'bef918f83b6a0d1e4f980013342807cf8',
            'b004cb9235acb5f689d20904692bc026e',
            'b869ff9519d67354816af90867f4a5425',
            'bcd8e9100dcb601f65e849c147e3e972e',
            'b0111919a698f9816862b4ae662a6ed06',
        ]

        prefix_2_keys = [
            'x37fbab0bd2e60563c79469e5be41e515',
            'x30c6eb2ad176773b5ce6d590d2472dfe',
            'x3d4fc9480f0a07b28aa7646d5066b54d',
            'x387c3d4ab7f0c1c6ef549198fc14b525',
            'x5c74dc83e132e435e8512599e1075bc0',
            'x1472425d0d9bb5ff511e132896d54b13',
            'x2cedb5c52163c22a0b5f179001959dd2',
            'x6223f65e553280cd25cadeac6657555c',
            'xeae18af37c223dde92a71fef55e64afe',
            'xb8810784ffb360cd3ffc57b1d088e537',
        ]

        keys = prefix_1_keys + prefix_2_keys
        random.shuffle(keys)

        for k in keys:
            self.dbset(k, k)

        keys.sort()

        got_keys = self.d.keys()

        self.assertListEqual(keys, got_keys)