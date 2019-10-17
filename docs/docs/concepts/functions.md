## @export
You have to define at least one `@export` decorated function in your smart contract. Otherwise, the smart contract has no functions for people to call.

```python
@export
def hello():
	return 1
```

This is probably one of the simplest contracts you can write. As long as there is a single `@export` function, you're good to go.

## Private Functions
Private functions are just functions without any decorators on them. They can be used internally by your smart contract, but cannot be called by people outside the system or by other smart contracts themselves.

```python
@export
def hello():
	return there()

def there():
	return 1
```

## @construct
If you want a smart contract to execute a piece of code once on submission, you can define a single function with the `@construct` decorator. The function you decorate can be called anything. Use this to set up an initial state for your smart contract.

```python
owner = Variable()

@construct
def seed():
	owner.set('stu')

@export
def get_owner():
	return owner.get()
```

The `seed` function will execute when the contract is submitted, but never again. Thus, the initial state is such that `owner` is set to `stu`. Because there are no other functions to change this variable in storage, this will stay static.

## Constructor Arguments
Sometimes, you may write a smart contract that you want to redeploy, or want to define the construction when you submit it. You can do this by providing keyword arguments to the `@construct` function you make.

```python
owner = Variable()
allowed = Variable()

@construct
def seed(initial_owner, intial_allowed):
	owner.set(initial_owner)
	allowed.set(intial_allowed)

@export
def get_owner():
	return owner.get()

@export
def get_allowed():
	return allowed.get()
```

Now when you submit the contract, you can specify the initial arguments and they will be set dynamically on submission. If you use the client, it would look something like this.

```python
from contracting.client import ContractingClient

def example():
	owner = Variable()
	allowed = Variable()

	@construct
	def seed(initial_owner, intial_allowed):
		owner.set(initial_owner)
		allowed.set(intial_allowed)

	@export
	def get_owner():
		return owner.get()

	@export
	def get_allowed():
		return allowed.get()

client = ContractingClient()
client.submit(example, constructor_args={
	'initial_owner': 'stu',
	'initial_allowed': 'raghu'
	})
```