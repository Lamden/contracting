## random Standard Library

`random` is a pseudorandom number generator that derives a deterministic seed state from the current block number and block height. In Contracting, these environment variables are not automatically supplied. The `ContractingClient` also does not current have support for this feature, so you will have to automatically update your environment with a block height and hash that you would like to use.

Simply do the following:
```python
def random_contract():
	@export
	def uses_random_function():
		...

client = ContractingClient()
client.submit(random_contract)

rc = client.get_contract('random_contract')
rc.uses_random_function(environment={
	'block_height': 0,
	'block_hash': 'any_string'
	})
```

#### random.seed()

This function is required to be run once per transaction. If it is not called, the contract will fail. You must seed every contract like so:

```python
def random_contract():
	random.seed()

	@export
	def random_one():
		...

	@export
	def random_two():
		...
```

#### Available functions

Besides seeding, the rest of the module follows Python random 1:1. Here are the functions you can use and reference the [Python manual](https://docs.python.org/3.6/library/random.html) to read more about how each one behaves.

```python
random.shuffle(l: list)
random.getrandbits(k: int)
random.randrange(k: int)
random.randint(a: int, b: int)
random.choice(l: list)
random.choices(l: list, k: int)
```