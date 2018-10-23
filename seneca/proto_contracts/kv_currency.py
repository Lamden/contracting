from seneca.engine.datatypes import *
from seneca.libs.constrain import constrain


class Context:
    def __init__(self, sender=None, author=None):
        self.sender = sender
        self.author = author


rt = Context()

balances = hmap('balances', str, int)
allowed = hmap('allowed', str, hmap(value_type=int))


def balance_of(wallet_id):
    return balances[wallet_id]


def transfer(to, amount):
    sender_balance = balances[rt.sender]
    assert sender_balance >= amount, 'Not enough funds!'

    balances[rt.sender] -= amount
    balances[to] += amount


def approve(spender, amount):
    allowed[rt.sender][spender] = amount


def transfer_from(_from, to, amount):
    assert allowed[_from][rt.sender] >= amount
    assert balances[_from] >= amount

    allowed[_from][rt.sender] -= amount
    balances[_from] -= amount
    balances[to] += amount


def allowance(approver, spender):
    return allowed[approver][spender]


def mint(to, amount):
    assert rt.sender == rt.author, 'Only the original contract author can mint!'

    balances[to] += amount


def tests():
    rt.sender = 'stu'
    rt.author = 'stu'

    mint('stu', 100)

    print(balance_of('stu'))

    transfer('ass', 10)

    print(balance_of('stu'))
    print(balance_of('ass'))

    print("rep of balances: {}".format(balances.rep()))
    # print("rep of balances[ass]: {}".format(balances['ass'].rep()))


def clean_up():
    balances['stu'] = 0
    balances['ass'] = 0


tests()
clean_up()
