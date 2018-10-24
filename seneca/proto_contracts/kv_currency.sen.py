from seneca.libs.datatypes import *

balances = hmap('balances', str, int)
allowed = hmap('allowed', str, hmap(value_type=int))

@export
def balance_of(wallet_id):
    return balances[wallet_id]

@export
def transfer(to, amount):
    sender_balance = balances[rt.sender]
    assert sender_balance >= amount, 'Not enough funds!'

    balances[rt.sender] -= amount
    balances[to] += amount

@export
def approve(spender, amount):
    allowed[rt.sender][spender] = amount

@export
def transfer_from(_from, to, amount):
    assert allowed[_from][rt.sender] >= amount
    assert balances[_from] >= amount

    allowed[_from][rt.sender] -= amount
    balances[_from] -= amount
    balances[to] += amount

@export
def allowance(approver, spender):
    return allowed[approver][spender]

@export
def mint(to, amount):
    assert rt.sender == rt.author, 'Only the original contract author can mint!'
    balances[to] += amount
