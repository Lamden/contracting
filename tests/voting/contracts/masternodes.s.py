import currency

max_nodes = Variable()
stake_amount = Variable()

staked = Hash(default_value=False)
nodes = Hash(default_value=False)


@construct
def seed():
    nodes['MN1'] = True
    nodes['MN2'] = True
    nodes['MN3'] = True
    nodes['MN4'] = True

    stake_amount.set(1_000_000)

    max_nodes.set(64)

@export
def stake():
    if not staked[ctx.caller]:
        s = stake_amount.get()
        currency.transfer_from(amount=s, to=ctx.this, main_account=ctx.caller)
        staked[ctx.caller] = True

@export
def unstake():
    if staked[ctx.caller] and not nodes[ctx.caller]:
        s = stake_amount.get()
        currency.transfer(amount=s, to=ctx.caller)
        del staked[ctx.caller]

@export
def current_nodes():
    return nodes.all()


def vote(vk):
    assert staked[ctx.ctx.caller], 'You cannot vote if you have not staked!'
