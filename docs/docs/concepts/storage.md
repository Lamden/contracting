## How It Works
Contracting stores state in a key-value storage system where each smart contract has it's own data space that cannot be accessed by other smart contracts besides through the `@export` functions.

When you submit a smart contract, keys are created to store the code and compiled bytecode of the contract. For example:

```python
owner = Variable()

@construct
def seed():
	owner.set(ctx.caller)
```

When submitted will create the following in state space:

Key	|	Value
-	| -
contract.\_\_compiled\_\_ | Python Bytecode
contract.\_\_code\_\_ | Python Code
contract.owner | ctx.caller at submission time

Storage follows a simple pattern such that each variable or hash stored is prefaced by the contract name and a period delimiter. If the variable has additional keys, they are appended to the end seperated by colons.

```
<contract_name>.<variable_name>
<contract_name>.<variable_name>:<key_0>:<key_1>:<key_2>...
```

## Encoding

Data is encoded as JSON in the state space. This means that you can store simple Python objects such as dictionaries, arrays, tuples, and even Datetime and Timedelta types (explained later.)

```python
player = Variable()
stats = {
	'name': 'Steve',
	'level': 100,
	'type': 'Mage',
	'health': 1000
}
player.set(stats)

steve = player.get()

steve['health'] -= 100
steve['health'] == 900 # True
```

```python
authorized_parties = Variable()
parties = ['steve', 'alex', 'stu', 'raghu', 'tejas']
authorized_parties.set(parties)

# This will fail if the contract sender isn't in the authorized parties list.
assert ctx.caller in authorized_parties.get()
```
## Storage Types

There are two types of storage: Variable and Hash. Variable only has a single storage slot. Hash allows for a dynamic amount of dimensions to be added to them. Hashes are great for data types such as balances or mappings.

```python
owner = Variable()
balances = Hash()

@export
def example():
	owner.set('hello')
	a = owner.get()

	balances['stu'] = 100
	a = balances['something']
```

### Variable API
```python
class Variable(Datum):
    def __init__(self, contract, name, driver: ContractDriver=driver, t=None):
        ...

    def set(self, value):
        ...

    def get(self):
        ...
```
#### \_\_init\_\_(self, contract, name, driver, t)
The \_\_init\_\_ arguments are automatically filled in for you during compilation and runtime. You do not have to provide any of them.

```python
def some_contract():
	owner = Variable()
```

This translates into:
```python
owner = Variable(contract='some_contract', name='owner')
```

Driver is pulled from the Runtime (`rt`) module when the contract is being executed. If you provide a type to `t`, the Variable object will make sure that whatever is being passed into `set` is the correct type.

#### set(self, value)

```python
def some_contract():
	owner = Variable()
	owner.set('stu')
```

Executes on contract runtime and sets the value for this variable. The above code causes the following key/value pair to be written into the state.

Key	|	Value
-	| -
some_contract.owner | stu

__NOTE:__ You have to use the `set` method to alter data. If you use standard `=`, it will just cause the object to be set to whatever you pass.

```python
owner = Variable()
owner
>> <Variable at 0x10577cda0>

owner = 5
owner
>> 5
```

#### get(self)
```python
def some_contract():
	owner = Variable()
	owner.set('stu')

	owner.get() == 'stu' # True
```

Returns the value that is stored at this Variable's state location.

__NOTE:__ The converse applies to the `get` function. Simply setting a variable to the Variable object will just copy the reference, not the underlying data.

```python
owner = Variable()
owner.set('stu')
owner.get()
>> 'stu'

a = owner
a
>> <Variable at 0x10577cda0>
```

### Hash API

```python
class Hash(Datum):
    def __init__(self, contract, name, driver: ContractDriver=driver, default_value=None):
        ...

    def set(self, key, value):
        ...

    def get(self, item):
        ...

    def all(self, *args):
        ...

    def clear(self, *args):
       ...

    def __setitem__(self, key, value):
        ...

    def __getitem__(self, key):
        ...
```

#### \_\_init\_\_(self, contract, name, driver, default_value)

Similar to Variable's \_\_init\_\_ except that a different keyword argument `default_value` allows you to set a value to return when the key does not exist. This is good for ledgers or applications where you need to have a base value.

```python
def some_contract():
	balances = Hash(default_value=0)
	balances['stu'] = 1_000_000

	balances['stu'] == 1_000_000 # True
	balances['raghu'] == 0 # True
```

#### set(self, key, value)

Equivalent to Variable's `get` but accepts an additional argument to specify the key. For example, the following code executed would result in the following state space.

```python
def some_contract():
	balances = Hash(default_value=0)
	balances.set('stu', 1_000_000)
	balances.set('raghu', 100)
	balances.set('tejas', 777)
```

Key	|	Value
-	| -
some_contract.balances:stu | 1,000,000
some_contract.balances:raghu | 100
some_contract.balances:tejas | 777

#### Multihashes

You can provide an arbitrary number of keys (up to 16) to `set` and it will react accordingly, writing data to the dimension of keys that you provided. For example:

```python
def subaccounts():
	balances = Hash(default_value=0)
	balances.set('stu', 1_000_000)
	balances.set(('stu', 'raghu'), 1_000)
	balances.set(('raghu', 'stu'), 555)
	balances.set(('stu', 'raghu', 'tejas'), 777)
```

This will create the following state space:

Key	|	Value
-	| -
subaccounts.balances:stu | 1,000,000
subaccounts.balances:stu:raghu | 1,000
subaccounts.balances:raghu:stu | 555
subaccounts.balances:stu:raghu:tejas | 777

#### get(self, key)

Inverse of `set`, where the value for a provided key is returned. If it is `None`, it will set it to the `default_value` provided on initialization.

```python
def some_contract():
	balances = Hash(default_value=0)
	balances.set('stu', 1_000_000)
	balances.set('raghu', 100)
	balances.set('tejas', 777)

	balances.get('stu') == 1_000_000 # True
	balances.get('raghu') == 100 # True
	balances.get('tejas') == 777 # True
```

The same caveat applies here 

#### Multihashes
Just like `set`, you retrieve data stored in multihashes by providing the list of keys used to write data to that location. Just like `get` with a single key, the default value will be returned if no value at the storage location is found.

```python
def subaccounts():
	balances = Hash(default_value=0)
	balances.set('stu', 1_000_000)
	balances.set(('stu', 'raghu'), 1_000)
	balances.set(('raghu', 'stu'), 555)
	balances.set(('stu', 'raghu', 'tejas'), 777)

	balances.get('stu') == 1_000_000 # True
	balances.get(('stu', 'raghu')) == 1_000 # True
	balances.get(('raghu', 'stu')) == 555 # True
	balances.get(('stu', 'raghu', 'tejas')) == 777 # True

	balances.get(('stu', 'raghu', 'tejas', 'steve')) == 0 # True
```

__NOTE:__ If storage returns a Python object or dictionary, modifications onto that dictionary will __not__ be synced to storage until you set the key to the altered value again. This is vitally important.
```python
owner = Hash(default_value=0)
owner.set('stu') = {
	'complex': 123,
	'object': 567
}

d = owner.get('stu') # Get the dictionary from storage
d['complex'] = 999 # Set a value on the retrieved dictionary
e = owner.get('stu') # Retrieve the same value for comparison

d['complex'] == e['complex'] # False
```

```python
owner = Hash(default_value=0)
owner.set('stu') = {
	'complex': 123,
	'object': 567
}

d = owner.get('stu') # Get the dictionary from storage
d['complex'] = 999 # Set a value on the retrieved dictionary

owner.set('stu', d) # Set storage location to the modified dictionary

e = owner.get('stu') # Retrieve the same value for comparison

d['complex'] == e['complex'] # True!
```


#### \_\_setitem\_\_(self, key, value):
Equal functionality to `set`, but allows slice notation for convenience. __This is less verbose and the preferred method of setting storage on a Hash.__

```python
def subaccounts():
	balances = Hash(default_value=0)
	balances['stu'] = 1_000_000
	balances['stu', 'raghu'] = 1_000
	balances['raghu', 'stu'] = 555
	balances['stu', 'raghu', 'tejas'] = 777
```

__NOTE:__ The problem that occurs with Variable's set does not occur with Hashes.
```python
owner = Hash(default_value=0)
owner['stu'] = 100
owner['stu']
>> 100
```

#### \_\_getitem\_\_(self, key):
Equal functionality to `set`, but allows slice notation for convenience. __This is less verbose and the preferred method of setting storage on a Hash.__

```python
def subaccounts():
	balances = Hash(default_value=0)
	balances['stu'] = 1_000_000
	balances['stu', 'raghu'] = 1_000
	balances['raghu', 'stu'] = 555
	balances['stu', 'raghu', 'tejas'] = 777

	balances['stu'] == 1_000_000 # True
	balances['stu', 'raghu'] == 1_000 # True
	balances['raghu', 'stu'] == 555 # True
	balances['stu', 'raghu', 'tejas'] == 777 # True

	balances['stu', 'raghu', 'tejas', 'steve'] == 0 # True
```

#### all(self, \*args):

Returns all of the values in a particular hash. For multihashes, it returns all values in that 'subset' of hashes. Assume the following state space:

Key	|	Value
-	| -
subaccounts.balances:stu | 1,000,000
subaccounts.balances:stu:raghu | 1,000
subaccounts.balances:stu:tejas | 555
subaccounts.balances:raghu | 777
subaccounts.balances:raghu:stu | 10_000
subaccounts.balances:raghu:tejas | 100_000

```python
balances.all()
>> [1000000, 1000, 555, 777, 10000, 100000]

balances.all('raghu')
>> [777, 10000, 100000]
```

#### clear(self, \*args)

Clears an entire hash or a section of a hash if the list of keys are provided. Assume the same state space:

Key	|	Value
-	| -
subaccounts.balances:stu | 1,000,000
subaccounts.balances:stu:raghu | 1,000
subaccounts.balances:stu:tejas | 555
subaccounts.balances:raghu | 777
subaccounts.balances:raghu:stu | 10_000
subaccounts.balances:raghu:tejas | 100_000

```python
balances.clear('stu')
balances.all() # None of Raghu's accounts are affected
>> [777, 10000, 100000]
```

```python
balances.clear()
balances.all() # All entries have been deleted
>> []
```
