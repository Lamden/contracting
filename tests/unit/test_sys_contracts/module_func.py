supply = Variable()
balances = Hash(default_value=0)

@construct
def seed():
    balances['test'] = 100
    supply.set(balances['test'])

@export
def test_func(status=None):
    return status

@export
def test_keymod(deduct):
    balances['test'] -= deduct
    return balances['test']
