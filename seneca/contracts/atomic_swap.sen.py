from seneca.libs.storage.datatypes import Hash, Table
from seneca.libs.crypto.hashing import hash_data
from seneca.libs.math.decimal import Decimal
from seneca.contracts.smart_contract import import_contract

swaps = Hash('swaps')
swap = Table('swap', {
	'initiator': str,
	'participant': str,
	'amount': Decimal,
	'token': str,
	'expiration': Decimal,
})


def initiate(initiator, participant, expiration, hashlock, token, amount):

	if not swaps[participant][hashlock]:

		token_contract = import_contract(token)
		print('atommic_swap: ...')
		assert token_contract.allowance(initiator, rt['contract']) >= amount, 'Not enough allowance to initiate swap.'
		token_contract.transfer_from(initiator, rt['contract'], amount)

		swaps[participant][hashlock] = swap.add_row({
			'initiator': initiator,
			'participant': participant,
			'amount': amount,
			'token': token,
			'expiration': expiration
		})


def redeem(secret):
	digest = hash_data(secret, 'sha3_256')
	if swaps[rt['sender']][digest]:
		s = swaps[rt['sender']][digest]
		assert s['participant'] == rt['sender'], 'Not authorized to redeem'

		token = import_contract(s['token'])
		token.transfer(rt['sender'], s['amount'])


def refund(participant, secret):
	digest = hash_data(secret, 'sha3_256')
	if swaps[participant][digest]:
		s = swaps[participant][digest]
		# TODO figure out time
		# assert s['expiration'] < now, 'The swap is expired.'
		assert s['initiator'] == rt['sender'], 'Cannot refund. You are not the initiator.'

		token = import_contract(s['token'])
		token.transfer(rt['sender'], s['amount'])
