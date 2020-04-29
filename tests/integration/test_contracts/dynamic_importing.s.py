@export
def balance_for_token(tok: str, account: str):
    t = importlib.import_module(tok)
    return t.balance_of(account=account)

@export
def only_erc20(tok: str, account: str):
    t = importlib.import_module(tok)
    assert enforce_erc20(t), 'You cannot use a non-ERC20 standard token!!'

    return t.balance_of(account=account)

@export
def is_erc20_compatible(tok: str):
    interface = [
        importlib.Func('transfer', args=('amount', 'to')),
        importlib.Func('balance_of', args=('account',)),
        importlib.Func('total_supply'),
        importlib.Func('allowance', args=('owner', 'spender')),
        importlib.Func('approve', args=('amount', 'to')),
        importlib.Func('transfer_from', args=('amount', 'to', 'main_account')),
        importlib.Var('supply', Variable),
        importlib.Var('balances', Hash)
    ]

    t = importlib.import_module(tok)

    return importlib.enforce_interface(t, interface)

def enforce_erc20(m):
    interface = [
        importlib.Func('transfer', args=('amount', 'to')),
        importlib.Func('balance_of', args=('account',)),
        importlib.Func('total_supply'),
        importlib.Func('allowance', args=('owner', 'spender')),
        importlib.Func('approve', args=('amount', 'to')),
        importlib.Func('transfer_from', args=('amount', 'to', 'main_account')),
        importlib.Var('supply', Variable),
        importlib.Var('balances', Hash)
    ]

    return importlib.enforce_interface(m, interface)