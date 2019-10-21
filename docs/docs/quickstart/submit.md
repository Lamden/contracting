## Contructors

Sometimes, you'll want to setup a particular state at the start of the smart contract. Imagine that you want to mint a certain amount of tokens to the creator of the smart contract.

To do so, you can provide a `@construct` decorator on top of a single function. This function will then be executed when the contract is submitted.

```python
def token():
	balances = Hash()

	@construct
	def mint():
		balances['stu'] = 100
```

If you want to provide arguments to the constructor, you can easily do so like so.

```python
def token():
	balances = Hash()

	@construct
	def mint(owner):
		balances[owner] = 100
```

Now you have to submit the contract and pass the arguments at submission time. Read more about this in the 'Functions' section in 'Key Concepts'.

```python
c = ContractingClient()
c.submit(token, constructor_args={
	'owner': 'stu'
	})
```

## Context

As you create more advanced smart contracts, you'll need a way to know who is sending the transaction or calling a function. This is where context comes into play. `ctx.caller` is a variable that is available in all smart contracts on default. It tells you who is calling the function.

`ctx.caller` changes to 'whoever' is calling the current function. Therefore, if a smart contract calls a function on another smart contract, the name of the caller is changed. `ctx.caller` is now the name of the calling smart contract while the function is executing. `ctx.caller` changes back when the scope is returned.

```python
def token():
	balances = Hash()

	@construct
	def mint():
		balances[ctx.caller] = 100

c = ContractingClient(signer='stu')
c.submit(token)

t = c.get_contract('token')
t.balances['stu']

>> 100
```

There are three other context variables that are explained in Key Concepts.

## Imports

Complex contracts will need to import functions from other smart contracts. You can import any smart contract by using the `import` keyword. The entire contract is available for you to call. Any `@export` function is now available for your contract to call. When you call a function on this imported contract, the `ctx.caller` will change to the name of your smart contract.

```python
def magic():
	@export
	def return_ctx:
		return ctx.caller

def another_contract():
	import magic

	@export
	def call_magic():
		return magic.return_ctx()

c = ContractingClient(signer='stu')
c.submit(magic)
c.submit(another_contract)

ac = c.get_contract('another_contract')
ac.call_magic()
>> 'another_contract'
```

Much deeper levels of importing can be accomplished as well. Read the Key Concepts for more.