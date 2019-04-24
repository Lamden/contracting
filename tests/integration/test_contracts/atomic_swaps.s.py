import currency

swaps = Hash()


def initiate(participant: str, expiration: datetime, hashlock: str, amount: float):

    assert currency.allowance(ctx.signer, ctx.this) >= amount, \
        'You cannot initiate an atomic swap without allowing {}' \
        'at least {} coins.'.format(ctx.this, amount)

    swaps[participant, hashlock] = [expiration, amount]

    currency.transfer_from(ctx.signer, ctx.this, amount)


def redeem(secret: str):

    hashlock = sha256(secret)

    expiration, amount = swaps[ctx.signer, hashlock]

    if expiration >= now:
        currency.transfer(ctx.signer, amount)
        swaps[ctx.signer, hashlock] = None # change this to respond to the del keyword?


def refund(participant, secret):

    hashlock = sha256(secret)

    expiration, amount = swaps[participant, hashlock]

    if expiration < now:
        currency.transfer(ctx.signer, amount)
        swaps[ctx.signer, hashlock] = None
