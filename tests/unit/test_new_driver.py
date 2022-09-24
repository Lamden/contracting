from contracting import config
from contracting.db.driver import Driver, InMemDriver, FSDriver
from contracting.db.encoder import MONGO_MAX_INT
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting.stdlib.bridge.time import Datetime, Timedelta
from decimal import Decimal
from unittest import TestCase
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

class TestDriver(TestCase):
    # Flush this sucker every test
    def setUp(self):
        self.d = Driver()
        self.d.flush()

    def tearDown(self):
        self.d.flush()

    def test_get_set(self):
        for v in TEST_DATA:
            self.d.set('b', v)

            b = self.d.get('b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)

    def test_delete(self):
        for v in TEST_DATA:
            self.d.set('b', v)

            b = self.d.get('b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)

            self.d.delete('b')

            b = self.d.get('b')
            self.assertIsNone(b)

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
            self.d.set(k, k)

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

    def test_set_object_returns_properly(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing', thing)

        t = self.d.get('thing')
        self.assertDictEqual(thing, t)

    def test_set_none_deletes(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        self.d.set('t', None)

        self.assertEqual(self.d.get('t'), None)

    def test_delete_sets_to_none(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        self.d.delete('t')

        self.assertEqual(self.d.get('t'), None)

    def test_getitem_works_like_get(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing', thing)

        t = self.d['thing']
        self.assertDictEqual(thing, t)

    def test_setitem_works_like_set(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d['thing'] = thing

        t = self.d['thing']
        self.assertDictEqual(thing, t)

    def test_delitem_works_like_del(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        del self.d['t']

        self.assertEqual(self.d.get('t'), None)

    def test_iter_with_length_returns_list_of_size_l(self):
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
            self.d.set(k, k)

        p1 = []

        for k in self.d.iter(prefix='b', length=3):
            p1.append(k)

        prefix_1_keys.sort()
        p1.sort()

        self.assertListEqual(prefix_1_keys[:3], p1)

        p2 = []

        for k in self.d.iter(prefix='x', length=5):
            p2.append(k)

        prefix_2_keys.sort()
        p2.sort()

        self.assertListEqual(prefix_2_keys[:5], p2)

    def test_key_error_if_getitem_doesnt_exist(self):
        with self.assertRaises(KeyError):
            print(self.d['thing'])

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
            self.d.set(k, k)

        keys.sort()

        got_keys = self.d.keys()

        self.assertListEqual(keys, got_keys)


class TestInMemDriver(TestCase):
    # Flush this sucker every test
    def setUp(self):
        self.d = InMemDriver()
        self.d.flush()

    def tearDown(self):
        self.d.flush()

    def test_get_set(self):
        for v in TEST_DATA:
            self.d.set('b', v)

            b = self.d.get('b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)

    def test_delete(self):
        for v in TEST_DATA:
            self.d.set('b', v)

            b = self.d.get('b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)

            self.d.delete('b')

            b = self.d.get('b')
            self.assertIsNone(b)

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
            self.d.set(k, k)

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

    def test_set_object_returns_properly(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing', thing)

        t = self.d.get('thing')
        self.assertDictEqual(thing, t)

    def test_set_none_deletes(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        self.d.set('t', None)

        self.assertEqual(self.d.get('t'), None)

    def test_delete_sets_to_none(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        self.d.delete('t')

        self.assertEqual(self.d.get('t'), None)

    def test_getitem_works_like_get(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing', thing)

        t = self.d['thing']
        self.assertDictEqual(thing, t)

    def test_setitem_works_like_set(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d['thing'] = thing

        t = self.d['thing']
        self.assertDictEqual(thing, t)

    def test_delitem_works_like_del(self):
        t = 123

        self.d.set('t', t)

        self.assertEqual(self.d.get('t'), 123)

        del self.d['t']

        self.assertEqual(self.d.get('t'), None)

    def test_iter_with_length_returns_list_of_size_l(self):
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
            self.d.set(k, k)

        p1 = []

        for k in self.d.iter(prefix='b', length=3):
            p1.append(k)

        prefix_1_keys.sort()
        p1.sort()

        self.assertListEqual(prefix_1_keys[:3], p1)

        p2 = []

        for k in self.d.iter(prefix='x', length=5):
            p2.append(k)

        prefix_2_keys.sort()
        p2.sort()

        self.assertListEqual(prefix_2_keys[:5], p2)

    def test_key_error_if_getitem_doesnt_exist(self):
        with self.assertRaises(KeyError):
            print(self.d['thing'])

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
            self.d.set(k, k)

        keys.sort()

        got_keys = self.d.keys()

        self.assertListEqual(keys, got_keys)


class TestFSDriver(TestCase):
    # Flush this sucker every test
    def setUp(self):
        self.d = FSDriver()
        self.block_num = 33

    def tearDown(self):
        self.d.flush()

    def test_get_set(self):
        for v in TEST_DATA:
            self.d.set('b.b', v)

            b = self.d.get('b.b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)
            self.assertEqual(self.d.get_block('b.b'), config.BLOCK_NUM_DEFAULT)

    def test_get_set_with_block_num(self):
        for v in TEST_DATA:
            self.d.set('b.b', v, block_num=self.block_num)

            b = self.d.get('b.b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)
            self.assertEqual(self.d.get_block('b.b'), self.block_num)

    def test_delete(self):
        for v in TEST_DATA:
            self.d.set('b.b', v)

            b = self.d.get('b.b')
            self.assertEqual(v, b) if not isinstance(v, dict) else self.assertDictEqual(v, b)
            self.assertEqual(self.d.get_block('b.b'), config.BLOCK_NUM_DEFAULT)

            self.d.delete('b.b')

            b = self.d.get('b.b')
            self.assertIsNone(b)
            self.assertEqual(self.d.get_block('b.b'), config.BLOCK_NUM_DEFAULT)

    def test_keys_with_prefix(self):

        prefix_1_keys = [
            'b77aa343e339bed78.1c7c2be1267cd597',
            'bc22ede6e6fb4046d.78bf2f9d1f8afdb6',
            'b93dbb37d993846d7.0b8a92779cbfbfe9',
            'be1a2783019de6ea7.ef169cc55e48a3ae',
            'b1fe8db32b9185d62.8f4c346f0455023e',
            'bef918f83b6a0d1e4.f980013342807cf8',
            'b004cb9235acb5f68.9d20904692bc026e',
            'b869ff9519d673548.16af90867f4a5425',
            'bcd8e9100dcb601f6.5e849c147e3e972e',
            'b0111919a698f9816.862b4ae662a6ed06',
        ]

        prefix_2_keys = [
            'x37fbab0bd2e60563.c79469e5be41e515',
            'x37fbab0bd2e60563.c79469e5be41e515:something',
            'x30c6eb2ad176773b.5ce6d590d2472dfe',
            'x3d4fc9480f0a07b2.8aa7646d5066b54d',
            'x387c3d4ab7f0c1c6.ef549198fc14b525',
            'x5c74dc83e132e435.e8512599e1075bc0',
            'x1472425d0d9bb5ff.511e132896d54b13',
            'x2cedb5c52163c22a.0b5f179001959dd2',
            'x6223f65e553280cd.25cadeac6657555c',
            'xeae18af37c223dde.92a71fef55e64afe',
            'xb8810784ffb360cd.3ffc57b1d088e537',
        ]

        keys = prefix_1_keys + prefix_2_keys
        random.shuffle(keys)

        for k in keys:
            self.d.set(k, k)

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

    def test_set_object_returns_properly(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing.thing', thing)

        t = self.d.get('thing.thing')
        self.assertDictEqual(thing, t)

    def test_set_none_deletes(self):
        t = 123

        self.d.set('t.t', t)

        self.assertEqual(self.d.get('t.t'), 123)

        self.d.set('t.t', None)

        self.assertEqual(self.d.get('t.t'), None)

    def test_delete_sets_to_none(self):
        t = 123

        self.d.set('t.t', t)

        self.assertEqual(self.d.get('t.t'), 123)

        self.d.delete('t.t')

        self.assertEqual(self.d.get('t.t'), None)

    def test_getitem_works_like_get(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d.set('thing.thing', thing)

        t = self.d['thing.thing']
        self.assertDictEqual(thing, t)

    def test_setitem_works_like_set(self):
        thing = {
            'a': 123,
            'b': False,
            'x': None
        }

        self.d['thing.thing'] = thing

        t = self.d['thing.thing']
        self.assertDictEqual(thing, t)

    def test_delitem_works_like_del(self):
        t = 123

        self.d.set('t.t', t)

        self.assertEqual(self.d.get('t.t'), 123)

        del self.d['t.t']

        self.assertEqual(self.d.get('t.t'), None)

    def test_keys_with_length_returns_list_of_size_l(self):
        prefix_1_keys = [
            'b77aa343e339bed7.81c7c2be1267cd597',
            'bc22ede6e6fb4046.d78bf2f9d1f8afdb6',
            'b93dbb37d993846d.70b8a92779cbfbfe9',
            'be1a2783019de6ea.7ef169cc55e48a3ae',
            'b1fe8db32b9185d6.28f4c346f0455023e',
            'bef918f83b6a0d1e.4f980013342807cf8',
            'b004cb9235acb5f6.89d20904692bc026e',
            'b869ff9519d67354.816af90867f4a5425',
            'bcd8e9100dcb601f.65e849c147e3e972e',
            'b0111919a698f981.6862b4ae662a6ed06',
        ]

        prefix_2_keys = [
            'x37fbab0bd2e6056.3c79469e5be41e515',
            'x30c6eb2ad176773.b5ce6d590d2472dfe',
            'x3d4fc9480f0a07b.28aa7646d5066b54d',
            'x387c3d4ab7f0c1c.6ef549198fc14b525',
            'x5c74dc83e132e43.5e8512599e1075bc0',
            'x1472425d0d9bb5f.f511e132896d54b13',
            'x2cedb5c52163c22.a0b5f179001959dd2',
            'x6223f65e553280c.d25cadeac6657555c',
            'xeae18af37c223dd.e92a71fef55e64afe',
            'xb8810784ffb360c.d3ffc57b1d088e537',
        ]

        keys = prefix_1_keys + prefix_2_keys
        random.shuffle(keys)

        for k in keys:
            self.d.set(k, k)

        p1 = []

        for k in self.d.iter(prefix='b', length=3):
            p1.append(k)

        prefix_1_keys.sort()
        p1.sort()

        self.assertListEqual(prefix_1_keys[:3], p1)

        p2 = []

        for k in self.d.iter(prefix='x', length=5):
            p2.append(k)

        prefix_2_keys.sort()
        p2.sort()

        self.assertListEqual(prefix_2_keys[:5], p2)

    def test_key_none_if_getitem_doesnt_exist(self):
        self.assertIsNone(self.d['thing.thing'])

    def test_keys_returns_all_keys(self):
        prefix_1_keys = [
            'b77aa343e339bed7.81c7c2be1267cd597',
            'bc22ede6e6fb4046.d78bf2f9d1f8afdb6',
            'b93dbb37d993846d.70b8a92779cbfbfe9',
            'be1a2783019de6ea.7ef169cc55e48a3ae',
            'b1fe8db32b9185d6.28f4c346f0455023e',
            'bef918f83b6a0d1e.4f980013342807cf8',
            'b004cb9235acb5f6.89d20904692bc026e',
            'b869ff9519d67354.816af90867f4a5425',
            'bcd8e9100dcb601f.65e849c147e3e972e',
            'b0111919a698f981.6862b4ae662a6ed06',
        ]

        prefix_2_keys = [
            'x37fbab0bd2e6056.3c79469e5be41e515',
            'x30c6eb2ad176773.b5ce6d590d2472dfe',
            'x3d4fc9480f0a07b.28aa7646d5066b54d',
            'x387c3d4ab7f0c1c.6ef549198fc14b525',
            'x5c74dc83e132e43.5e8512599e1075bc0',
            'x1472425d0d9bb5f.f511e132896d54b13',
            'x2cedb5c52163c22.a0b5f179001959dd2',
            'x6223f65e553280c.d25cadeac6657555c',
            'xeae18af37c223dd.e92a71fef55e64afe',
            'xb8810784ffb360c.d3ffc57b1d088e537',
        ]

        keys = prefix_1_keys + prefix_2_keys
        random.shuffle(keys)

        for k in keys:
            self.d.set(k, k)

        keys.sort()

        got_keys = self.d.keys()

        self.assertListEqual(keys, got_keys)
