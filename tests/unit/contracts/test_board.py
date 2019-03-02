# from seneca.tooling import *
# from decimal import Decimal
# from unittest import TestCase, main
# import seneca, os
#
# path = os.path.dirname(seneca.__path__[0])
#
# class TestBoard(TestCase):
# 	def setUp(self):
# 		f = open('{}/test_contracts/tau.sen.py'.format(path))
#
# 		default_interface.r.flushdb()
# 		default_interface.publish_code_str(fullname='tau', author='stu', code_str=f.read())
#
# 		f.close()
#
# 		f = open('{}/test_contracts/board.sen.py'.format(path))
# 		default_interface.publish_code_str(fullname='board', author='stu', code_str=f.read())
# 		f.close()
# 		self.board = ContractWrapper(contract_name='board', driver=default_interface, default_sender='stu')
# 		self.tau = ContractWrapper(contract_name='tau', driver=default_interface, default_sender='stu')
#
# 	def test_coor_str(self):
# 		res = self.board.coor_str(x=1, y=0)
# 		self.assertEqual(res['output'], '1,0')
#
# 	def test_buy_pixel(self):
# 		res = self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=1000)
# 		self.assertEqual(res['status'], 'success')
# 		self.assertTrue(default_interface.r.exists('tau:balances:stu'))
# 		self.assertTrue(default_interface.r.exists('board:colors:0,0'))
#
# 	def test_buy_pixel(self):
# 		self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=1000)
# 		self.tau.add_to_custodial(to='board', amount=100000, sender='davis')
# 		self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=10000, sender='davis')
#
# 		davis_custodial = self.tau.get_custodial(owner='davis', spender='board')['output']
# 		davis_balance = self.tau.get_balance(account='davis')['output']
#
# 		self.assertEqual(davis_custodial, Decimal('100000') - Decimal('1000'))
# 		self.assertEqual(davis_balance, Decimal('900000'))
#
# 	def test_bad_buy_pixel(self):
# 		self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=1000000000)
# 		with self.assertRaises(AssertionError):
# 			self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=10000, sender='davis')
#
# 	def test_buy_out_of_bounds_pixel(self):
# 		with self.assertRaises(AssertionError):
# 			self.board.buy_pixel(x=999, y=999, r=255, g=255, b=0, new_price=1000000000)
#
# 	def test_buy_out_of_bounds_pixel_negative(self):
# 		with self.assertRaises(AssertionError):
# 			self.board.buy_pixel(x=-999, y=-999, r=255, g=255, b=0, new_price=1000000000)
#
# 	def test_price_pixel(self):
# 		self.board.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=1000)
# 		self.board.price_pixel(x=0, y=0, new_price=1234)
#
# 		self.assertEqual(self.board.price_of_pixel(x=0, y=0)['output'], Decimal('1234'))
#
# 	def test_price_pixel_not_owned_fails(self):
# 		with self.assertRaises(AssertionError):
# 			self.board.price_pixel(x=0, y=0, new_price=1234)
#
# if __name__ == "__main__":
# 	main()
