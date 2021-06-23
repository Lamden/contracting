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

    def test_soft_apply_adds_changes_to_pending_deltas(self):
        self.c.set('thing1', 9999)

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)

        expected_deltas = {
            '0': {
                'thing1': (9999, 8888)
            }
        }

        self.assertDictEqual(self.c.pending_deltas, expected_deltas)

    def test_soft_apply_applies_the_changes_to_the_driver_but_not_hard_driver(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)

        res = self.c.get('thing1')

        self.assertEqual(res, 8888)
        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_hard_apply_applies_hcl_if_exists(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)
        self.c.hard_apply('0')

        res = self.c.get('thing1')

        self.assertEqual(res, 8888)

        self.assertEqual(self.c.driver.get('thing1'), 8888)

    def test_hard_apply_only_applies_changes_up_to_delta(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)

        state_changes = {
            'thing1': 7777
        }

        self.c.soft_apply('1', state_changes)

        state_changes = {
            'thing1': 6666
        }

        self.c.soft_apply('2', state_changes)

        self.c.hard_apply('1')

        res = self.c.get('thing1')

        self.assertEqual(res, 7777)

        self.assertEqual(self.c.driver.get('thing1'), 7777)

    def test_hard_apply_removes_hcls(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)

        state_changes = {
            'thing1': 7777
        }

        self.c.soft_apply('1', state_changes)

        state_changes = {
            'thing1': 6666
        }

        self.c.soft_apply('2', state_changes)

        self.c.hard_apply('0')

        hcls = {
            '1': {
                'thing1': (8888, 7777)
            },
            '2': {
                'thing1': (7777, 6666)
            }
        }

        self.assertDictEqual(self.c.pending_deltas, hcls)

    def test_rollback_returns_to_initial_state(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)
        self.assertEqual(self.c.get('thing1'), 8888)

        state_changes = {
            'thing1': 7777
        }

        self.c.soft_apply('1', state_changes)
        self.assertEqual(self.c.get('thing1'), 7777)

        state_changes = {
            'thing1': 6666
        }

        self.c.soft_apply('2', state_changes)
        self.assertEqual(self.c.get('thing1'), 6666)

        self.c.rollback()

        self.assertEqual(self.c.get('thing1'), 9999)
        self.assertEqual(self.c.driver.get('thing1'), 9999)

    def test_rollback_removes_hlcs(self):
        self.c.set('thing1', 9999)
        self.c.commit()

        state_changes = {
            'thing1': 8888
        }

        self.c.soft_apply('0', state_changes)
        self.assertEqual(self.c.get('thing1'), 8888)

        state_changes = {
            'thing1': 7777
        }

        self.c.soft_apply('1', state_changes)
        self.assertEqual(self.c.get('thing1'), 7777)

        state_changes = {
            'thing1': 6666
        }

        self.c.soft_apply('2', state_changes)
        self.assertEqual(self.c.get('thing1'), 6666)

        self.c.rollback()

        self.assertDictEqual(self.c.pending_deltas, {})
