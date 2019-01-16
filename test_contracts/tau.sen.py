from seneca.libs.datatypes import hmap

balances = hmap('balances', str, int)

@export
def transfer(to, amount):
    print('transfer', balances[rt['sender']], rt['sender'])
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
    assert custodials[_from][rt['sender']] >= amount, 'Not enough funds to transfer from "{}" to "{}"'.format(_from, rt['sender'])

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
    balances['davis'] = 1000000
