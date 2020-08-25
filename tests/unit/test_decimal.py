from decimal import Decimal
import decimal
import math

from contracting.stdlib.bridge.decimal import Fixed, pop_digits, pop_zeros, build_num_string
from contracting.stdlib.bridge.decimal import ContractingDecimal
from unittest import TestCase


class TestDecimal(TestCase):
    def test_init(self):
        ContractingDecimal('1.1')

    def test_init_float(self):
        ContractingDecimal(1.2)

    def test_init_int(self):
        ContractingDecimal(1)

    def test_bool_true(self):
        self.assertTrue(ContractingDecimal(1))

    def test_bool_false(self):
        self.assertFalse(ContractingDecimal(0))

    def test_eq_whole_numbers(self):
        self.assertEqual(ContractingDecimal(1), ContractingDecimal(1))

    def test_eq_floats(self):
        self.assertEqual(ContractingDecimal(1.234), ContractingDecimal(1.234))

    def test_lt(self):
        self.assertLess(ContractingDecimal(1), ContractingDecimal(2))
        self.assertLess(ContractingDecimal(1.1), ContractingDecimal(2.2))

    def test_lte(self):
        self.assertLessEqual(ContractingDecimal(1), ContractingDecimal(2))
        self.assertLessEqual(ContractingDecimal(1.1), ContractingDecimal(2.2))
        self.assertLessEqual(ContractingDecimal(2.2), ContractingDecimal(2.2))

    def test_gt(self):
        self.assertGreater(ContractingDecimal(10), ContractingDecimal(2))
        self.assertGreater(ContractingDecimal(10.1), ContractingDecimal(2.2))

    def test_gte(self):
        self.assertGreaterEqual(ContractingDecimal(10), ContractingDecimal(2))
        self.assertGreaterEqual(ContractingDecimal(10.1), ContractingDecimal(2.2))
        self.assertGreaterEqual(ContractingDecimal(2.2), ContractingDecimal(2.2))

    def test_str(self):
        f = ContractingDecimal(1.23445)
        self.assertEqual(str(f), '1.23445')

    def test_neg(self):
        self.assertEqual(-ContractingDecimal(1), ContractingDecimal(-1))

    def test_pos(self):
        self.assertEqual(+ContractingDecimal(1), ContractingDecimal(1))

    def test_other_equality(self):
        self.assertEqual(ContractingDecimal(1), 1)
        self.assertEqual(ContractingDecimal(1), 1.0)

    def test_abs(self):
        self.assertEqual(abs(ContractingDecimal(1)), 1)
        self.assertEqual(abs(ContractingDecimal(-1)), 1)

    def test_add(self):
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(1), 2)
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(10), 11)

        self.assertEqual(ContractingDecimal(1.23456) + ContractingDecimal(6.54321), ContractingDecimal(7.77777))

    def test_arbitrarily_large_number(self):
        a = ContractingDecimal('38327950288419716939937510.582097494459230781640628620899')
        b = ContractingDecimal('67523846748184676694051320.005681271452635608277857713427')
        c = ContractingDecimal('105851797036604393633988830.587778765911866389918486334326')

        self.assertEqual(a + b, c)

    def test_zero_equality(self):
        self.assertEqual(ContractingDecimal(0), 0)

    def test_sub(self):
        self.assertEqual(ContractingDecimal(1) - ContractingDecimal(1), 0)
        self.assertEqual(ContractingDecimal(1) - ContractingDecimal(10), -9)

        self.assertEqual(ContractingDecimal(1.23456) - ContractingDecimal(6.54321), ContractingDecimal(-5.30865))

    def test_add_negs(self):
        self.assertEqual(ContractingDecimal(1) + ContractingDecimal(-1), 0)

    def test_radd(self):
        self.assertEqual(1 + ContractingDecimal(1), 2)
        self.assertEqual(1 + ContractingDecimal(10), 11)

        self.assertEqual(1.23456 + ContractingDecimal(6.54321), ContractingDecimal(7.77777))

    def test_rsub(self):
        self.assertEqual(1 - ContractingDecimal(1), 0)
        self.assertEqual(1 - ContractingDecimal(10), -9)

        self.assertEqual(1.23456 - ContractingDecimal(6.54321), ContractingDecimal(-5.30865))

    def test_float_eq(self):
        self.assertEqual(Decimal('12.01488534'), Decimal(12.01488534))

    def test_mul(self):
        self.assertEqual(ContractingDecimal(5) * ContractingDecimal(42), 210)
        self.assertEqual(ContractingDecimal(0) * ContractingDecimal(100), 0)
        self.assertEqual(ContractingDecimal(-5) * ContractingDecimal(42), -210)
        self.assertEqual(ContractingDecimal(5.1234) * ContractingDecimal(2.3451), 12.01488534)

    def test_rmul(self):
        self.assertEqual(5 * ContractingDecimal(42), 210)
        self.assertEqual(0 * ContractingDecimal(100), 0)
        self.assertEqual(-5 * ContractingDecimal(42), -210)
        self.assertEqual(5.1234 * ContractingDecimal(2.3451), 12.01488534)

    def test_div(self):
        self.assertEqual((ContractingDecimal(1) / ContractingDecimal(3)), ContractingDecimal('0.333333333333333333333333333333'))
        self.assertEqual(ContractingDecimal(3) / ContractingDecimal(1), 3)

    def test_div_large_decimals(self):
        a = '0.78164062862089986280348253421170'
        b = '0.53642401735797937714409102114816'

        c = ContractingDecimal(a) / ContractingDecimal(b)

        print(c)

    def test_pop_digits_0_does_nothing(self):
        a = 123456

        b = pop_digits(a, 0)

        self.assertEqual(a, b)

    def test_pop_digits_2_removes_2_from_back(self):
        a = 123456

        b = pop_digits(a, 2)

        self.assertEqual(b, 1234)

    def test_pop_zeros_whole_numbers_unaffected(self):
        n = pop_zeros('123000')
        self.assertEqual(n, '123000')

    def test_pop_zeros_adds_zero_back_if_hits_decimal(self):
        n = pop_zeros('1.00000000000')
        self.assertEqual(n, '1.0')

    def test_pop_zeros_keeps_rest_of_decimal(self):
        n = pop_zeros('1.12300000000')
        self.assertEqual(n, '1.123')

    def test_build_num_str_fails_if_denom_zero(self):
        with self.assertRaises(AssertionError):
            build_num_string(1, 0)

    def test_build_num_str_fails_if_denom_not_factor_of_10(self):
        with self.assertRaises(AssertionError):
            build_num_string(1, 2)

    def test_build_num_str_works_as_expected(self):
        # 123.456
        n = 123456
        d = 1000

        self.assertEqual(build_num_string(n, d), '123.456')

    def test_build_num_str_removes_zeros(self):
        # 123.456
        n = 123456 * (10 ** 16)
        d = 1000 * (10 ** 16)

        self.assertEqual(build_num_string(n, d), '123.456')

