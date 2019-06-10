@export
def balance_for_token(tok, account):
    t = importlib.import_module(tok)
    return t.balance_of(account=account)

@export
def is_erc20_compatible(tok):
    interface = [
        importlib.Func('transfer', args=('amount', 'to')),
        importlib.Func('balance_of', args=('account',)),
        importlib.Func('total_supply'),
        importlib.Func('allowance', args=('owner', 'spender')),
        importlib.Func('approve', args=('amount', 'to')),
        importlib.Func('private_func', private=True),
        importlib.Func('transfer_from', args=('amount', 'to', 'main_account')),
        importlib.Var('supply', Variable),
        importlib.Var('balances', Hash)
    ]

    t = importlib.import_module(tok)

    return importlib.enforce_interface(t, interface)