# Seneca - Smart Contracts with Python

<img src="https://github.com/Lamden/seneca/raw/master/seneca.jpg" align="right"
     title="Seneca" width="300" height="450">

Smart contracts allow people to develop open agreements to do business in a way that is completely transparent, auditable, and automatable. Traditionally, smart contracting languages have been difficult for people to pick up. This is because early smart contract systems expose the differences between themselves and general programming languages through the development experience.

Seneca is different because it focuses on the developer's point of view to provide an interface that feels as close to coding traditional systems as possible.

## Install and Get Started

`coming soon`

## Data Driven Model

Most web based applications are driven by data: usernames, passwords, email addresses, profile pictures, etc. etc. However, smart contracts today do not provide clear interfaces to storing these complex data models.

Seneca treats data like a tabular SQL table and smart contracts as a group of methods that creates, reads, updates, and deletes that data. This provides a very smooth development experience and a shallow learning curve to smart contracting.

```
ledger = st.create_table('ledger', [
    ('wallet_id', st.str_len(200), True),
    ('balance', int),
])

ledger.insert([{'wallet_id': 'carl', 'balance': 1000000}]).run()
```

## Clear Syntax

Seneca is Python. We restrict a lot of functionality, such as infinite loops, random number generation, etc., because it does not play well with the concepts found in the blockchain realm. But, the core syntax is 100% valid Python. You can run Seneca code on a plain MySQL database instance with the standard Python interpreter and it will function exactly as it will on the blockchain.

## Straightforward Extendability

Users (people like you!) are assigned a namespace which their smart contracts live on the blockchain based on their public key. This means that publishing smart contracts live in an open namespace that others can link to from their own smart contracts.

```
from carls_public_key import token

token.transfer_coins('carl', 100)
```

If you want to keep your smart contracts off limits, you can use our easy to use permissioning systems or simply not export the methods of your smart contract to the world. Methods on smart contracts are private by default so that permissioning hacks, [like the ones that Parity suffered](https://medium.com/@rtaylor30/how-i-snatched-your-153-037-eth-after-a-bad-tinder-date-d1d84422a50b), are less likely to occur.

```
...

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
    
...
```

## Why the name Seneca?

Seneca was a Roman Stoic philosopher. The Stoics practiced logic, level-headedness, pragmatism, and critical thinking over emotion. We wanted to create a smart contracting language that was straightforward, made logical sense, and took few ideological stances.
