from seneca.libs.datatypes import hmap

balances = hmap('balances', str, int)

@seed
def deposit_to_all_wallets():
    balances['cat'] = 1000000


def balance_of(wallet_id):
    return balances[wallet_id]

@export
def transfer(to, amount):
    print("transfering from {} to {} with amount {}".format(rt['sender'], to, amount))
    balances[rt['sender']] -= amount
    balances[to] += amount
    sender_balance = balances[rt['sender']]

    assert sender_balance >= 0, "Sender balance must be non-negative!!!"
