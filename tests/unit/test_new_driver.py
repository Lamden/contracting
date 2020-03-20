from unittest import TestCase
from contracting.db.driver import Driver, InMemDriver
import random


class TestDriver(TestCase):
    # Flush this sucker every test
    def setUp(self):
        self.d = Driver()
        self.d.flush()

    def tearDown(self):
        self.d.flush()

    def test_get_set(self):
        a = 'a'
        self.d.set('b', a)

        b = self.d.get('b')
        self.assertEqual(a, b)

    def test_delete(self):
        a = 'a'
        self.d.set('b', a)

        b = self.d.get('b')
        self.assertEqual(a, b)

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
        a = 'a'
        self.d.set('b', a)

        b = self.d.get('b')
        self.assertEqual(a, b)

    def test_delete(self):
        a = 'a'
        self.d.set('b', a)

        b = self.d.get('b')
        self.assertEqual(a, b)

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
