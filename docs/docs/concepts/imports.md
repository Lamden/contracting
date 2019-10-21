## Static Imports

The simplest use-case for imports is wanting to call a function that is an `@export` of another function. This is the cornerstone for abstraction and interesting applications. To do this, you simply have to use the `import` keyword and the name of the smart contract.

__NOTE:__ `from x import y` and starred imports are not supported at this time. Importing a smart contract imports all of the `@export` functions from it and none of the variables.

```python
def complex_app():
	@export
	def return_1():
		return 1

	@export
	def return_2():
		return 2

	@export
	def return_3():
		return 3

def import_example():
	import complex_app

	@export
	def calculate():
		a = complex_app.return_2()
		b = complex_app.return_3()

		return a * b
```

Believe it or not, `calculate` will return 6.

### Dynamic Imports

Things get interesting when you want to reference contracts that don't exist at the moment, but will potentially in the future. An example of this could be an exchange application where different assets register to the exchange and can be automatically listed and interacted with if they fit a certain profile.

To do this, we have to use the `importlib` in the Contracting standard library.

#### importlib.import_module(name)

This function behaves similar to the analogous `importlib` function included in the Python standard library. Calling it will return a module object that has only the `@export` functions available to call and pass arguments to.

```python
def token_1():
	balances = Hash()
	@construct
	def seed():
		balances['stu'] = 100

	@export
	def send(amount, to):
		assert balances[ctx.caller] >= amount

		balances[ctx.caller] -= amount
		balances[to] += amount

def token_2():
	balances = Hash()
	@construct
	def seed():
		balances['stu'] = 100

	@export
	def send(amount, to):
		assert balances[ctx.caller] >= amount

		balances[ctx.caller] -= amount
		balances[to] += amount

def exchange():
	@export
	def send(token, amount, to):
		t = importlib.import_module(token)
		t.send(amount, to)
```

Luckily, both contracts have the same interface and have a function called `send` which takes two arguments. How can you tell if this is not the case?

### Interface Enforcement

A smart contract can define an interface to enforce contracts against. Enforcement can be on the functions and/or the variables. Enforcement is 'weak' in the sense that a contract can have additional functions or variables and still succeed an interface test.

```python
def exchange():
	token_interface = [
		importlib.Func('send', args=('amount', 'to')),
		importlib.Var('balances', Hash)
	]

	@export
	def send(token, amount, to):
		t = importlib.import_module(token)
		assert importlib.enforce_interface(t, token_interface)

		t.send(amount, to)
```

#### importlib.enforce_interface(module, interface)

`enforce_interface` takes two arguments and returns a boolean of whether or not the module fits the interface. An interface is a list of functions and variables that a module must have defined.

#### importlib.Func(name, args=None, private=False)

A function definition for an interface list. If a function has no arguments, then none have to be provided. `args` must be a tuple of strings indicating the keyword arguments in the correct order. Enforcement will fail if arguments on a function are misspelled or out of order. `private` will define the required function as a private function that does not have an `@export` decorator above it.

#### importlib.Var(name, t)

A variable definition for the name, a string, and the type, which is either Variable or Hash at this point in time.

#### Examples

```python
interface_1 = [
	importlib.Func('something', private=True)
]

def valid_contract():
	def something(): # Correct name and private
		return 123

	@export
	def something_else():
		return 456

def invalid_contract():
	@export
	def something(): # Correct name, but exported
		return 123
```
```python
interface_2 = [
	importlib.Func('func', args=('a', 'b', 'c'))
]

def valid_contract():
	@export
	def func(a, b, c): # Exported function with same name and args in correct order
		return a + b + c

def invalid_contract():
	def func(a, c, b): # Correct name, but private, and keyword arguments are out of order
		return a + b + c

	@export
	def not_func(a, b, c): # Exported and correct keyword args but not the right name
		return a + b + c
```
```python
interface_3 = [
	importlib.Var('balances', Hash),
	importlib.Var('owner', Variable)
]

def valid_contract():
	balances = Hash()
	owner = Variable()

def invalid_contract():
	balances = Variable() # Incorrect types
	owner = Hash()

def invalid_contract_2():
	bbb = Variable() # Correct types, but misspelled.
	ooo = Hash()
```