from unittest import TestCase
from seneca.libs.metering.cost import Cost
import unittest

class TestCosts(TestCase):

    def setUp(self):
        self.c = Cost()
        self.c.pre()

    def tearDown(self):
        self.c.post()

    def test_cost_1(self):
        self.assertEqual(self.c.compute_cost(self.c.compile('''
a = 1
a = 2
a = 4
a = 1
        ''')), 18)

    def test_cost_2(self):
        self.assertEqual(self.c.compute_cost(self.c.compile('''
balances = {'hello': 'world'}
balances['hello'] = 'goodbye'
        ''')), 10)

    def test_cost_3(self):
        self.assertEqual(self.c.compute_cost(self.c.compile('''
balances = {'hello': 'world'}
for i in range(100):
    balances['hello'] = 'goodbye'
        ''')), 511)

    def test_cost_4(self):
        self.assertEqual(self.c.compute_cost(self.c.compile('''
balances = {'hello': 'world'}
for i in range(1000):
        balances['hello'] = 'goodbye'
        ''')), 5011)

    def test_cost_5(self):
        self.assertEqual(self.c.compute_cost(self.c.compile('''
a=(0,1,2,3, ... ,65535)
        ''')), 6)

if __name__ == '__main__':
    unittest.main()
