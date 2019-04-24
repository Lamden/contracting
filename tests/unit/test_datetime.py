from unittest import TestCase
from seneca.stdlib.bridge.time import Datetime
from datetime import datetime as dt
from datetime import timedelta


class TestDatetime(TestCase):
    def test_datetime_variables_set(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        self.assertEqual(now.microsecond, d.microsecond)
        self.assertEqual(now.second, d.second)
        self.assertEqual(now.minute, d.minute)
        self.assertEqual(now.hour, d.hour)
        self.assertEqual(now.day, d.day)
        self.assertEqual(now.month, d.month)
        self.assertEqual(now.year, d.year)

    ###
    # ==
    ###
    def test_datetime_eq_true(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)
        e = Datetime(now_str)

        self.assertTrue(d == e)

    def test_datetime_eq_false(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertFalse(d == e)

    ###
    # !=
    ###
    def test_datetime_ne_false(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)
        e = Datetime(now_str)

        self.assertFalse(d != e)

    def test_datetime_ne_true(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertTrue(d != e)

    ###
    # <
    ###
    def test_datetime_lt_true(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertTrue(d < e)

    def test_datetime_lt_false(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertFalse(e < d)

    ###
    # >
    ###
    def test_datetime_gt_true(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertTrue(e > d)

    def test_datetime_gt_false(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertFalse(d > e)

    ###
    # >=
    ###
    def test_datetime_ge_true_g(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertTrue(e >= d)

    def test_datetime_ge_true_eq(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)
        e = Datetime(now_str)

        self.assertTrue(d >= e)

    def test_datetime_ge_false_g(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertFalse(d >= e)

    ###
    # <=
    ###
    def test_datetime_le_true(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertTrue(d <= e)

    def test_datetime_le_true_eq(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)
        e = Datetime(now_str)

        self.assertTrue(d <= e)

    def test_datetime_le_false(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        then = now + timedelta(days=1)
        then_str = dt.isoformat(then)

        e = Datetime(then_str)

        self.assertFalse(e <= d)