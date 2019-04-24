supply = Variable()
balances = Hash(default_value=0)

@seneca_construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100
    supply.set(balances['stu'] + balances['colin'])

@seneca_export
def transfer(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount
    balances[to] += amount

@seneca_export
def balance_of(account):
    return balances[account]

@seneca_export
def total_supply():
    return supply.get()

@seneca_export
def allowance(owner, spender):
    return balances[owner, spender]

@seneca_export
def approve(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    # Example of the multihash capabilities
    balances[sender] -= amount
    balances[sender, to] += amount

@seneca_export
def transfer_from(account, to, amount):
    sender = ctx.signer
    assert balances[account, sender] >= amount, 'Not enough coins to send!'

    balances[account, sender] -= amount
    balances[to] += amount