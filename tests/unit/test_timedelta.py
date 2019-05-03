from unittest import TestCase
from contracting.stdlib.bridge.time import Timedelta, WEEKS, DAYS, HOURS, MINUTES, SECONDS
from datetime import datetime as dt
from datetime import timedelta
import decimal

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

    def test_ne_true(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=1)

        self.assertTrue(t != _t)

    def test_ne_false(self):
        t = Timedelta(days=10)
        _t = Timedelta(days=10)

        self.assertFalse(t != _t)

    def test_addition_works_days(self):
        t_add = Timedelta(days=10) + Timedelta(days=1)
        t_done = Timedelta(days=11)
        org = timedelta(days=11)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_addition_works_seconds(self):
        t_add = Timedelta(seconds=10) + Timedelta(seconds=1)
        t_done = Timedelta(seconds=11)
        org = timedelta(seconds=11)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_addition_works_days_and_seconds(self):
        t_add = Timedelta(days=10, seconds=10) + Timedelta(days=1, seconds=1)
        t_done = Timedelta(days=11, seconds=11)
        org = timedelta(days=11, seconds=11)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_subtraction_works_days(self):
        t_add = Timedelta(days=10) - Timedelta(days=1)
        t_done = Timedelta(days=9)
        org = timedelta(days=9)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_subtraction_works_seconds(self):
        t_add = Timedelta(seconds=10) - Timedelta(seconds=1)
        t_done = Timedelta(seconds=9)
        org = timedelta(seconds=9)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_subtraction_works_days_and_seconds(self):
        t_add = Timedelta(days=10, seconds=10) - Timedelta(days=1, seconds=1)
        t_done = Timedelta(days=9, seconds=9)
        org = timedelta(days=9, seconds=9)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_multiplication_works(self):
        t_add = Timedelta(days=10) * Timedelta(days=3)
        t_done = Timedelta(days=30)
        org = timedelta(days=30)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_multiplication_works_seconds(self):
        t_add = Timedelta(seconds=10) * Timedelta(seconds=3)
        t_done = Timedelta(seconds=30)
        org = timedelta(seconds=30)

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_multiplication_works_days_and_seconds(self):
        SECONDS_IN_A_DAY = 86400

        t_add = Timedelta(days=10, seconds=10) * Timedelta(days=3, seconds=3)
        t_done = Timedelta(seconds=(30 + (30*SECONDS_IN_A_DAY)))
        org = timedelta(seconds=(30 + (30*SECONDS_IN_A_DAY)))

        self.assertEqual(t_add, t_done)
        self.assertEqual(t_add._timedelta, org)

    def test_addition_not_implemented(self):
        with self.assertRaises(TypeError):
            Timedelta(days=10, seconds=10) + 5

    def test_subtraction_not_implemented(self):
        with self.assertRaises(TypeError):
            Timedelta(days=10, seconds=10) - 5

    def test_multiplication_with_int_works(self):
        self.assertEqual(Timedelta(days=10, seconds=10) * 5, Timedelta(days=50, seconds=50))
        self.assertEqual((Timedelta(days=10, seconds=10) * 5)._timedelta, timedelta(days=50, seconds=50))

    def test_multiplication_does_not_work_with_decimal(self):
        with self.assertRaises(TypeError):
            Timedelta(days=10, seconds=10) * decimal.Decimal(0.1)