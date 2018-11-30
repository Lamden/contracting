from seneca.libs.importing import import_contract

@export
def import_stuff():
    token_a = import_contract('cat_cash')
    print(token_a.balance_of('cat'))
    return token_a