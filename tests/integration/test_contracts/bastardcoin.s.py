balances = Hash(default_value=0)

@construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100
    supply.set(balances['stu'] + balances['colin'])

@export
def transfer(amount, to):
    sender = ctx.caller
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount
