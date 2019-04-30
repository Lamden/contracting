supply = Variable()
balances = Hash(default_value=0)

@construct
def seed():
    balances['stu'] = 1000000
    balances['colin'] = 100
    supply.set(balances['stu'] + balances['colin'])

@export
def transfer(amount, to):
    sender = ctx.signer

    balances[sender] -= amount
    balances[to] += amount

    # putting the assert down here shouldn't matter to the execution and data environment
    assert balances[sender] >= amount, 'Not enough coins to send!'

@export
def balance_of(account):
    return balances[account]