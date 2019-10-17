## What is Contracting?
Contracting is a system that brings the ease of Python into the complex world of smart contracts and distributed systems. Here's how it looks:
```python
balances = Hash()
owner = Variable()

@construct
def seed():
    owner.set(ctx.caller)
    balances[ctx.caller] = 1_000_000

@export
def transfer(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount, 'Not enough coins to send!'

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@export
def balance(account):
    return balances[account]

```

### Applications
1. Contracting is the language that is used in the Lamden blockchain system and you want to develop smart contracts for that blockchain system.
2. You want to deploy your own instance of a database that uses smart contract 'apps' to control traditional CRUD type operations.
3. You really like Python and want to learn as much as possible.

### Value Proposition

Contracting focuses on developer experience (DX) which is a major focus of the Python language as a whole.

Our goal is to create a development experience that is clear, concises, and manageable so that you don't have to worry about what makes smart contracts hard, and just have to worry about what makes your smart contract great.

We take inspiration from some of these Python libraries:

* Requests
* Keras
* PyTorch
