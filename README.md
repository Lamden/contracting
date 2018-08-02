# Seneca - Smart Contracts with Python

<img src="https://github.com/Lamden/seneca/raw/master/seneca.jpg" align="right"
     title="Seneca" width="300" height="450">

Smart contracts allow people to develop open agreements to do business in a way that is completely transparent, auditable, and automatable. Traditionally, smart contracting languages have been difficult for people to pick up. This is because early smart contract systems expose the differences between themselves and general programming languages through the development experience.

Seneca is different because it focuses on the developer's point of view to provide an interface that feels as close to coding traditional systems as possible. Here's an example:

```
import seneca.storage.tabular as st
import seneca.crypto as crypto
import seneca.runtime as rt
import seneca.stdlib as std
from seneca.modulelib import export, make_exports

ledger = st.create_table('ledger', [
    ('wallet_id', st.str_len(200), True),
    ('balance', int),
])

allowed = st.create_table('allowed', [
    ('owner_id', st.str_len(200)),
    ('spender_id', st.str_len(200)),
    ('amount', int),
])

@export
def get_balance(wallet_id=None):
    if not wallet_id:
        wallet_id = rt.global_run_data.author
    return ledger.select('balance').where(ledger.wallet_id == wallet_id).run()[0]['balance']

@export
def wallet_exists(wallet_id):
    query = ledger.select('wallet_id').where(ledger.wallet_id == wallet_id)
    return len(query.run()) == 1

@export
def create_wallet(wallet_id):
    assert not wallet_exists(wallet_id), "Wallet already exists"
    ledger.insert([{'wallet_id': wallet_id, 'balance': 0}]).run()

def add_coins(wallet_id, amount_to_add):
    assert amount_to_add >= 0, "It's not possible to 'add' a negative balance"

    if not wallet_exists(wallet_id):
        create_wallet(wallet_id)

    old_balance = get_balance(wallet_id)
    ledger.update({'balance': old_balance + amount_to_add}) \
        .where(ledger.wallet_id == wallet_id).run()


def remove_coins(wallet_id, amount_to_remove):
    assert wallet_exists(wallet_id), "Wallet id is not present in ledger"
    assert amount_to_remove >= 0, "Removing negative balances not permitted"

    old_balance = get_balance(wallet_id)
    assert old_balance - amount_to_remove >= 0, "No negative balances allowed"
    ledger.update({'balance': old_balance - amount_to_remove}) \
        .where(ledger.wallet_id == wallet_id).run()

@export
def transfer_coins(receiver_id, amount):
    sender_id = rt.global_run_data.author
    _transfer_coins(sender_id, receiver_id, amount)

def _transfer_coins(sender_id, receiver_id, amount):
    assert wallet_exists(sender_id), "Wallet id is not present in ledger"
    assert wallet_exists(receiver_id), "Wallet id is not present in ledger"
    remove_coins(sender_id, amount)
    add_coins(receiver_id, amount)
```
