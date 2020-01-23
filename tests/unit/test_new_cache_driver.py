from unittest import TestCase
from contracting.db.driver import CacheDriver, Driver


class TestCacheDriver(TestCase):
    def setUp(self):
        self.d = Driver()
        self.d.flush()

        self.c = CacheDriver(self.d)

    def test_get_adds_to_read(self):
        self.c.get('thing')
        self.assertTrue('thing' in self.c.reads)

    def test_set_adds_to_cache_and_pending_writes(self):
        self.c.set('thing', 1234)
        self.assertEqual(self.c.cache['thing'], 1234)
        self.assertEqual(self.c.pending_writes['thing'], 1234)

    def test_object_added_to_cache_if_read_from_db(self):
        self.assertIsNone(self.c.cache.get('thing'))

        self.d.set('thing', 8999)

        self.c.get('thing')

        self.assertEqual(self.c.cache['thing'], 8999)

    def test_object_in_cache_returns_from_cache(self):
        self.d.set('thing', 8999)
        self.c.get('thing')
        self.assertEqual(self.c.get('thing'), 8999)

    def test_commit_puts_all_objects_in_pending_writes_to_db(self):
        self.c.set('thing1', 1234)
        self.c.set('thing2', 1235)
        self.c.set('thing3', 1236)
        self.c.set('thing4', 1237)
        self.c.set('thing5', 1238)

        self.assertIsNone(self.d.get('thing1'))
        self.assertIsNone(self.d.get('thing2'))
        self.assertIsNone(self.d.get('thing3'))
        self.assertIsNone(self.d.get('thing4'))
        self.assertIsNone(self.d.get('thing5'))

        self.c.commit()

        self.assertEqual(self.d.get('thing1'), 1234)
        self.assertEqual(self.d.get('thing2'), 1235)
        self.assertEqual(self.d.get('thing3'), 1236)
        self.assertEqual(self.d.get('thing4'), 1237)
        self.assertEqual(self.d.get('thing5'), 1238)

    def test_clear_pending_state_resets_all_variables(self):
        self.c.set('thing1', 1234)
        self.c.set('thing2', 1235)
        self.c.get('something')

        self.assertTrue(len(self.c.cache) > 0)
        self.assertTrue(len(self.c.reads) > 0)
        self.assertTrue(len(self.c.pending_writes) > 0)

        self.c.clear_pending_state()

        self.assertFalse(len(self.c.cache) > 0)
        self.assertFalse(len(self.c.reads) > 0)
        self.assertFalse(len(self.c.pending_writes) > 0)