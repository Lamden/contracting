from unittest import TestCase
from seneca.libs.metering.cost import Cost
import unittest

class TestCosts(TestCase):

    def setUp(self):
        self.c = Cost()

    def test_cost_1(self):
        self.assertEqual(self.c.compute_cost('''
a = 1
a = 2
a = 4
a = 1
        '''), 2944)

    def test_cost_2(self):
        self.assertEqual(self.c.compute_cost('''
balances = {'hello': 'world'}
balances['hello'] = 'goodbye'
        '''), 1448)

    def test_cost_3(self):
        self.assertEqual(self.c.compute_cost('''
balances = {'hello': 'world'}
for i in range(100):
    balances['hello'] = 'goodbye'
        '''), 153318)

    def test_cost_4(self):
        self.assertEqual(self.c.compute_cost('''
balances = {'hello': 'world'}
for i in range(1000):
        balances['hello'] = 'goodbye'
        '''), 1519518)

    def test_cost_5(self):
        self.assertEqual(self.c.compute_cost('''
a=(0,1,2,3, ... ,65535)
        '''), 703)

if __name__ == '__main__':
    unittest.main()
