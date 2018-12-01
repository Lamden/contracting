from seneca.libs.importing import import_contract

@export
def get_token_balance(token_name, account):
    token = import_contract(token_name)
    return token.balance_of(account)