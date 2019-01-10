from seneca.tooling import *
from unittest import TestCase, main
import seneca, os

path = os.path.dirname(seneca.__path__[0])

class TestBoard(TestCase):
	def setUp(self):
		f = open('{}/test_contracts/tau.sen.py'.format(path))

		default_driver.r.flushdb()
		default_driver.publish_code_str(fullname='tau', author='stu', code_str=f.read())

		f.close()

		f = open('{}/test_contracts/board.sen.py'.format(path))
		default_driver.publish_code_str(fullname='board', author='stu', code_str=f.read())
		f.close()
		self.contract = ContractWrapper(contract_name='board', driver=default_driver, default_sender='stu')

	#def test_coor_str(self):
	#	print(self.contract.coor_str(x=1, y=0))

	def test_buy_pixel(self):
		print(self.contract.buy_pixel(x=0, y=0, r=255, g=255, b=0, new_price=1000))

main()
