# Quick Start
For this quick 'how-to', we will be using [Jupyter Notebook](https://jupyter.org/). Jupyter is a great tool for Python programmers to develop and explore in as they combine the high feedback of a REPL with the presentation and saving of a program.

If you are a Python programmer, chances are you already have Jupyter installed. If not, follow [this guide](https://jupyter.readthedocs.io/en/latest/install.html) to get started. After that, just start the notebook:

```
jupyter notebook
```

## Import the Client
Contracting has a super high level client that allows you to develop smart contracts without any knowledge of the underlying mechanics of the execution system. This makes it perfect for new comers to the library.

```python
from contracting.client import ContractingClient
client = ContractingClient()
```
If initializing the `client` hangs, that means your database is not running and Contracting can't connect to where it stores data.

## Hello, World!
The following will be our first smart contract. Recreate it in your notebook.

```python
def hello_world():
	@export
	def hello():
		return 'World!'

	@export
	def add(a, b):
		return private_add(a, b)

	def private_add(a, b):
		return a + b
```

Off the bat, notice two things:

 1. The smart contract is a closure (a function inside of a function)
 2. There is an `@export` decorator.

 This will make sense in a bit. For now, notice them and let's submit this into the smart contracting 'state space.'

```python
client.submit(hello_world)
client.get_contracts()
```
```pythyon
>> ['hello_world', 'submission']
```

If the `'hello_world'` contract now appears in the returned list, you've successfully submitted your first smart contract. Congrats!

*NOTE:* For submitting closures, the name of the contract is automatically taken from the name of the closure. `def my_func():` becomes `my_func` in the smart contract state space, etc.
