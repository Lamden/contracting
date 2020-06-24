import erc20

@export
def double_spend(reciever: str):
    allowance = erc20.allowance(owner=ctx.caller, spender=ctx.this)
    erc20.transfer_from(amount=allowance, to=reciever, main_account=ctx.caller)

    i = 0
    while True:
        i += 1
