from seneca.tooling import *
from unittest import TestCase, main
from decimal import Decimal

def tau():
	from seneca.libs.datatypes import hmap

	balances = hmap('balances', str, int)

	@export
	def transfer(to, amount):
	    assert balances[rt['sender']] >= amount

	    balances[to] += amount
	    balances[rt['sender']] -= amount

	# a better way to deal with 'allowances' which are dumb af
	# and don't reflect real life business operations
	custodials = hmap('custodials', str, hmap(key_type=str, value_type=int))

	@export
	def add_to_custodial(to, amount):
		assert balances[rt['sender']] >= amount

		custodials[rt['sender']][to] += amount
		balances[rt['sender']] -= amount

	@export
	def remove_from_custodial(to, amount):
		assert custodials[rt['sender']][to] >= amount

		balances[rt['sender']] += amount
		custodials[rt['sender']][to] -= amount

	@export
	def spend_custodial(_from, amount, to):
		assert custodials[_from][rt['sender']] >= amount, 'Not enough in custodial account to spend.'

		balances[to] += amount
		custodials[_from][rt['sender']] -= amount

	@export
	def get_balance(account):
		return balances[account]

	@export
	def get_custodial(owner, spender):
		return custodials[owner][spender]

	@seed
	def seed():
		balances['stu'] = 1000000

CONTRACT_NAME = 'tau'
CONTRACT_AUTHOR = 'stu'

class TestTau(TestCase):
	def setUp(self):
		default_driver.r.flushdb()
		self.contract = publish_function(tau, 'tau', 'stu')

	def test_get_balance(self):
		stu_balance = self.contract.get_balance(account='stu')['output']
		self.assertEqual(stu_balance, Decimal('1000000'))

	def test_transfer(self):
		self.contract.transfer(to='falcon', amount=500)
		stu_balance = self.contract.get_balance(account='falcon')['output']
		self.assertEqual(stu_balance, Decimal('500'))

	def test_custodial(self):
		self.contract.add_to_custodial(to='falcon', amount=420)
		falcon_custodial = self.contract.get_custodial(owner='stu', spender='falcon')['output']
		self.assertEqual(falcon_custodial, Decimal('420'))

	def test_custodial_remove(self):
		self.contract.add_to_custodial(to='falcon', amount=420)
		falcon_custodial = self.contract.get_custodial(owner='stu', spender='falcon')['output']
		self.assertEqual(falcon_custodial, Decimal('420'))

		self.contract.remove_from_custodial(to='falcon', amount=100)
		falcon_custodial = self.contract.get_custodial(owner='stu', spender='falcon')['output']
		self.assertEqual(falcon_custodial, Decimal('320'))

	def test_custodial_spend(self):
		self.contract.add_to_custodial(to='falcon', amount=420)
		self.contract.spend_custodial(_from='stu', to='davis', amount=123, sender='falcon')
		davis_balance = self.contract.get_balance(account='davis')['output']

		self.assertEqual(davis_balance, Decimal('123'))

	def test_unavailable_custodial_spend(self):
		with self.assertRaises(AssertionError):
			output = self.contract.spend_custodial(_from='stu', to='davis', amount=123, sender='falcon')

	def test_too_large_custodial_spend(self):
		self.contract.add_to_custodial(to='falcon', amount=420)
		with self.assertRaises(AssertionError):
			self.contract.spend_custodial(_from='stu', to='davis', amount=500, sender='falcon')

if __name__ == "__main__":
	main()
