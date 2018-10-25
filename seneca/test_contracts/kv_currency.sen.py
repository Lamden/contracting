from seneca.libs.datatypes import *


balances = hmap('balances', str, int)
allowed = hmap('allowed', str, hmap(value_type=int))


@export
def balance_of(wallet_id):
    return balances[wallet_id]


@export
def transfer(to, amount):
    print("transfering from {} to {} with amount {}".format(rt.sender, to, amount))
    sender_balance = balances[rt.sender]

    balances[rt.sender] -= amount
    balances[to] += amount

    assert balances[rt.sender] > 0, "Sender balance must be greater than 0!!!"


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


# def tests():
#     rt.sender = 'stu'
#     rt.author = 'stu'
#
#     mint('stu', 100)
#
#     print(balance_of('stu'))
#
#     transfer('ass', 10)
#
#     print(balance_of('stu'))
#     print(balance_of('ass'))
#
#     print("rep of balances: {}".format(balances.rep()))
#
#
# def clean_up():
#     balances['stu'] = 0
#     balances['ass'] = 0
#
#
# tests()
# clean_up()
