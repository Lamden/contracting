from unittest import TestCase
from contracting.db.encoder import encode, decode, safe_repr
from contracting.stdlib.bridge.time import Datetime, Timedelta
from datetime import datetime
from decimal import Decimal
from contracting.stdlib.bridge.decimal import ContractingDecimal, fixed


class TestDecimal(TestCase):
    def test_init_str(self):
        a = ContractingDecimal('1.2345')
        self.assertEqual(a, fixed(1.2345))

    def test_init_float(self):
        a = ContractingDecimal(3.333333333334)
        self.assertEqual(a, fixed(3.333333333334))

    def test_init_fpbinary(self):
        a = ContractingDecimal(fixed(3.333333333334))
        self.assertEqual(a, fixed(3.333333333334))

    def test_bool_true_false(self):
        a = ContractingDecimal(1)
        self.assertTrue(bool(a))

        b = ContractingDecimal(-1)
        self.assertFalse(bool(b))

    def test_eq_on_float(self):
        a = ContractingDecimal(1.1111111)
        self.assertEqual(a, 1.1111111)

    def test_eq_on_decimal(self):
        a = ContractingDecimal(1.1111111)
        b = Decimal('1.1111111')
        self.assertEqual(a, b)

    def test_lt(self):
        a = ContractingDecimal(-2)

        b = -1
        c = Decimal(-1)
        d = ContractingDecimal(-1)

        self.assertTrue(a < b)
        self.assertTrue(a < c)
        self.assertTrue(a < d)

    def test_lt_false(self):
        a = ContractingDecimal(-2)

        b = -3
        c = Decimal(-3)
        d = ContractingDecimal(-3)

        self.assertFalse(a < b)
        self.assertFalse(a < c)
        self.assertFalse(a < d)

    def test_lte(self):
        a = ContractingDecimal(-2)

        b = -1
        c = Decimal(-1)
        d = ContractingDecimal(-1)

        self.assertTrue(a <= b)
        self.assertTrue(a <= c)
        self.assertTrue(a <= d)

        a = ContractingDecimal(-1)

        b = -1
        c = Decimal(-1)
        d = ContractingDecimal(-1)

        self.assertTrue(a <= b)
        self.assertTrue(a <= c)
        self.assertTrue(a <= d)

    def test_lte_false(self):
        a = ContractingDecimal(-2)

        b = -3
        c = Decimal(-3)
        d = ContractingDecimal(-3)

        self.assertFalse(a <= b)
        self.assertFalse(a <= c)
        self.assertFalse(a <= d)

    def test_gt(self):
        a = ContractingDecimal(2)

        b = -1
        c = Decimal(-1)
        d = ContractingDecimal(-1)

        self.assertTrue(a > b)
        self.assertTrue(a > c)
        self.assertTrue(a > d)

    def test_gte(self):
        a = ContractingDecimal(2)

        b = -1
        c = Decimal(-1)
        d = ContractingDecimal(-1)

        self.assertTrue(a >= b)
        self.assertTrue(a >= c)
        self.assertTrue(a >= d)

        a = ContractingDecimal(2)

        b = 2
        c = Decimal(2)
        d = ContractingDecimal(2)

        self.assertTrue(a >= b)
        self.assertTrue(a >= c)
        self.assertTrue(a >= d)

    def test_gt_false(self):
        a = ContractingDecimal(2)

        b = 4
        c = Decimal(4)
        d = ContractingDecimal(4)

        self.assertFalse(a > b)
        self.assertFalse(a > c)
        self.assertFalse(a > d)

    def test_gte_false(self):
        a = ContractingDecimal(2)

        b = 4
        c = Decimal(4)
        d = ContractingDecimal(4)

        self.assertFalse(a >= b)
        self.assertFalse(a >= c)
        self.assertFalse(a >= d)

    def test_str(self):
        a = ContractingDecimal(1.2345)
        self.assertEqual(str(a), '1.2345')

    def test_neg(self):
        a = ContractingDecimal(-123.456)

        self.assertEqual(-a, 123.456)

    def test_pos(self):
        a = ContractingDecimal(123.456)
        self.assertEqual(+a, 123.456)

        a = ContractingDecimal(-123.456)
        self.assertEqual(+a, -123.456)

    def test_abs(self):
        a = ContractingDecimal(123.456)
        self.assertEqual(abs(a), 123.456)

        a = ContractingDecimal(-123.456)
        self.assertEqual(abs(a), 123.456)

    def test_add(self):
        a = ContractingDecimal(1.234)
        b = ContractingDecimal(3.456)

        self.assertEqual(a + b, 1.234 + 3.456)

