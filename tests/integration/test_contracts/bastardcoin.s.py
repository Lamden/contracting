balances = Hash(default_value=0)

@construct
def seed():
    balances['stu'] = 999
    balances['colin'] = 555

@export
def transfer(amount, to):
    sender = ctx.caller
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount

@export
def balance_of(account):
    return balances[account]