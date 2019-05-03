from unittest import TestCase
from contracting.stdlib.bridge.time import Timedelta, WEEKS, DAYS, HOURS, MINUTES, SECONDS
from datetime import datetime as dt
from datetime import timedelta


class TestTimedelta(TestCase):
    def test_implementation_mimics_actual_timedelta(self):
        t = Timedelta(days=10, minutes=10, seconds=10)
        _t = timedelta(days=10, minutes=10, seconds=10)

        self.assertEqual(t._timedelta, _t)

    def test_constants_work(self):
        self.assertEqual(WEEKS._timedelta, timedelta(weeks=1))
        self.assertEqual(DAYS._timedelta, timedelta(days=1))
        self.assertEqual(HOURS._timedelta, timedelta(hours=1))
        self.assertEqual(MINUTES._timedelta, timedelta(minutes=1))
        self.assertEqual(SECONDS._timedelta, timedelta(seconds=1))

    def test_eq_true(self):
        t = Timedelta(days=1)
        _t = Timedelta(days=1)

        self.assertTrue(t == _t)

    def test_eq_false(self):
        t = Timedelta(days=1)
        _t = Timedelta(days=10)

        self.assertFalse(t == _t)

    def test_gt_true(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertTrue(t > _t)

    def test_gt_false(self):
        t = Timedelta(days=1)
        _t = Timedelta(days=10)

        self.assertFalse(t > _t)

    def test_ge_true(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertTrue(t >= _t)

    def test_ge_false(self):
        t = Timedelta(days=1)
        _t = Timedelta(days=10)

        self.assertFalse(t >= _t)

    def test_ge_true_eq(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=10)

        self.assertTrue(t >= _t)

    def test_lt_true(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertFalse(t < _t)

    def test_lt_false(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertFalse(t < _t)

    def test_le_true(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertFalse(t <= _t)

    def test_le_false(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertFalse(t <= _t)

    def test_le_true_eq(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=10)

        self.assertTrue(t <= _t)
