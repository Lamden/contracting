import currency

staked = Hash()
stake_amount = Variable()

EPOCH_LENGTH = 100_000
EPOCH = block_num // EPOCH_LENGTH

@export
def seed():
    stake_amount.set(100_000)

@export
def stake(amount):
    currency.transfer_from(amount, ctx.caller, ctx.this)
    staked[EPOCH, ctx.caller] += amount

@export
def unstake(epoch, amount):
    assert epoch > EPOCH, 'Cannot unstake during the current epoch!'

    stake_balance = staked[epoch, ctx.caller]

    assert amount <= stake_balance, 'Trying to unstake more than you have staked!'

    currency.transfer_from(amount, ctx.caller)
    staked[epoch, ctx.caller] -= amount

@export
def is_staked(epoch, account):
    return staked[epoch, ctx.caller] >= stake_amount.get()
