from seneca.redis_importer import hmap, table
import hashlib

swaps = hmap('swaps', str, hmap(None, str, table(None, {
	'initiator': str,
	'participant': str,
	'amount': int,
	'token': str,
	'expiration': int,
})))

def initiate(_initiator: str,
	_participant: str,
	_expiration: int,
	_hashlock: bytes,
	_token: str,
	_amount: int):
	if not swaps[_participant][_hashlock].exists():

		# dynamic import of token
		token = importlib.import_module(_token)
		assert token.allowance(rt['sender'], rt['contract_address']) >= _amount
		token.transfer_from(rt['sender'], rt['contract_address'], _amount)

		swaps[_participant][_hashlock] = {
			'initiator': _initiator,
			'participant': _participant,
			'amount': _amount,
			'token': _token,
			'expiration': _expiration
		}

def redeem(secret: bytes):
	digest = hashlib.sha3_256().update(secret).digest()
	if swaps[rt['sender']][digest].exists():
		s = swaps[rt['sender']][digest]
		assert s['participant'] == rt['sender']

		token = importlib.import_module(s['token'])
		token.transfer(rt['sender'], s['value'])

def refund(secret: bytes):
	digest = hashlib.sha3_256().update(secret).digest()
	if swaps[rt['sender']][digest].exists():
		s = swaps[rt['sender']][digest]
		assert s['expiration'] < now
		assert s['initiator'] == rt['sender']

		token = importlib.import_module(s['token'])
		token.transfer(rt['sender'], s['value'])
