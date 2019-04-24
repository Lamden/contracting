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

    balances[sender] -= amount
    balances[to] += amount

    # putting the assert down here shouldn't matter to the execution and data environment
    assert balances[sender] >= amount, 'Not enough coins to send!'

@seneca_export
def balance_of(account):
    return balances[account]