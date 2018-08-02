# Seneca - Smart Contracts with Python

<img src="https://github.com/Lamden/seneca/raw/master/seneca.jpg" align="right"
     title="Seneca" width="300" height="450">

Smart contracts allow people to develop open agreements to do business in a way that is completely transparent, auditable, and automatable. Traditionally, smart contracting languages have been difficult for people to pick up. This is because early smart contract systems expose the differences between themselves and general programming languages through the development experience.

Seneca is different because it focuses on the developer's point of view to provide an interface that feels as close to coding traditional systems as possible.

## Data Driven Model

Most web based applications are driven by data: usernames, passwords, email addresses, profile pictures, etc. etc. However, smart contracts today do not provide clear interfaces to storing these complex data models.

Seneca treats data like a tabular SQL table and smart contracts like the group of methods that create, read, update, and delete those records. This provides a very smooth development experience and a shallow learning curve to smart contracting.

```
ledger = st.create_table('ledger', [
    ('wallet_id', st.str_len(200), True),
    ('balance', int),
])

ledger.insert([{'wallet_id': 'carl', 'balance': 1000000}]).run()
```
