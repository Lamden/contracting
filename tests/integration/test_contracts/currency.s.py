balances = Hash()

@seneca_construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100

@seneca_export
def transfer(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@seneca_export
def balance(account):
    return balances[account]
