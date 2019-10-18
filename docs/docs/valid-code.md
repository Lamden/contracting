## No Classes Allowed!
Contracting maintains a strict 'no classes' model. This forces you as the developer to create more procedural code that is explicit and completely self-contained. Contracts must be easy to read and understand for validity. Instead of thinking of your code in classes, think of each contract as a 'module' that exposes certain functions to it's users.

All `class` keywords will fail your contract on submission. Even if you try to use classes for object oriented code, you will have to find another way to express your structures.

For example:

```python
class Car:
	def __init__(self, make, model):
		self.make = make
		self.model = model
```

This is illegal. Instead, describe objects in dictionary formats. If you tend to use classes to encapsulate data, simply use Python dictionaries instead. This is especially useful because of Contracting's storage model that makes it easy to store dictionaries.

```python
cars = Hash()
cars['balthasar'] = {
	'make': 'Ford',
	'model': 'Contour'
}
```

Read more about storage in the Storage section.

## Restricted Builtins

Certain builtins such as `exec`, `eval`, and `compile` are obviously dangerous. We do not want to allow any arbitrary execution of code.

Here is a full list of Python3.6 builtin functions versus the ones we allow in Contracting. NOTE: All exceptions except the base Exception class are removed from Contracting.

Built-Ins	|	Python3.6	|	Contracting	| Reason for Restriction
-	|	-	|	-	|	-	
[abs()](https://docs.python.org/3/library/functions.html#abs)						|	✓	|	✓	|	
[all()](https://docs.python.org/3/library/functions.html#all)						|	✓	|	✓	|	
[any()](https://docs.python.org/3/library/functions.html#any)						|	✓	|	✓	|
[ascii()](https://docs.python.org/3/library/functions.html#ascii)					|	✓	|	✓	|
[bin()](https://docs.python.org/3/library/functions.html#bin)						|	✓	|	✓	|
[bool()](https://docs.python.org/3/library/functions.html#bool)						|	✓	|	✓	|
[bytearray()](https://docs.python.org/3/library/functions.html#func-bytearray)		|	✓	|	✓	|
[bytes()](https://docs.python.org/3/library/functions.html#func-bytes)				|	✓	|	✓	|
[callable()](https://docs.python.org/3/library/functions.html#callable)				|	✓	|	✘	| Functions are not passed as objects in Contracting.
[chr()](https://docs.python.org/3/library/functions.html#chr)						|	✓	|	✓	|
[classmethod()](https://docs.python.org/3/library/functions.html#classmethod)		|	✓	|	✘	| Classes are disabled in Contracting.
[compile()](https://docs.python.org/3/library/functions.html#compile)				|	✓	|	✘	| Arbitrary code execution is a high security risk.
[complex()](https://docs.python.org/3/library/functions.html#complex)				|	✓	|	✘	| Complex numbers are potentially non-deterministic. This is a consensus failure risk.
[copyright](https://docs.python.org/3/library/constants.html#copyright)				|	✓	|	✘	| Unnecessary.
[credits](https://docs.python.org/3/library/constants.html#credits)					|	✓	|	✘	| Unnecessary.
[delattr()](https://docs.python.org/3/library/functions.html#delattr)				|	✓	|	✘	| Arbitrary removal of Python attributes could allow unauthorized access to private objects and methods.
[dict()](https://docs.python.org/3/library/functions.html#func-dict)				|	✓	|	✓	|
[dir()](https://docs.python.org/3/library/functions.html#dir)						|	✓	|	✘	| Allows exploration path into security exploit development.
[divmod()](https://docs.python.org/3/library/functions.html#divmod)					|	✓	|	✓	|
[enumerate()](https://docs.python.org/3/library/functions.html#enumerate)			|	✓	|	✘	| Potentially safe. Evaluating to make sure.
[eval()](https://docs.python.org/3/library/functions.html#eval)						|	✓	|	✘	| Arbitrary code execution is a high security risk.
[exec()](https://docs.python.org/3/library/functions.html#exec)						|	✓	|	✘	| Arbitrary code execution is a high security risk.
[filter()](https://docs.python.org/3/library/functions.html#filter)					|	✓	|	✓	|
[float()](https://docs.python.org/3/library/functions.html#float)					|	✓	|	✘	| Floating point precision is non-deterministic. This is a consensus failure risk.
[format()](https://docs.python.org/3/library/functions.html#format)					|	✓	|	✓	|
[frozenset()](https://docs.python.org/3/library/functions.html#func-frozenset)		|	✓	|	✓	|
[getattr()](https://docs.python.org/3/library/functions.html#getattr)				|	✓	|	✘	| Arbitrary access to attributes could allow private function execution.
[globals()](https://docs.python.org/3/library/functions.html#globals)				|	✓	|	✘	| Access to global scope methods allows modification of private methods and direct storage mechanisms.
[hasattr()](https://docs.python.org/3/library/functions.html#hasattr)				|	✓	|	✘	| Allows exploration path into security exploit development.
[hash()](https://docs.python.org/3/library/functions.html#hash)						|	✓	|	✘	| Potentially non-deterministic outcomes. Consensus failure risk.
[help()](https://docs.python.org/3/library/functions.html#help)						|	✓	|	✘	| Unnecessary.
[hex()](https://docs.python.org/3/library/functions.html#hex)						|	✓	|	✓	|
[id()](https://docs.python.org/3/library/functions.html#id)							|	✓	|	✘	| Potentially non-deterministic outcomes. Consensus failure risk.
[input()](https://docs.python.org/3/library/functions.html#input)					|	✓	|	✘	| User input not supported.
[int()](https://docs.python.org/3/library/functions.html#int)						|	✓	|	✓	|
[isinstance()](https://docs.python.org/3/library/functions.html#isinstance)			|	✓	|	✓	|
[issubclass()](https://docs.python.org/3/library/functions.html#issubclass)			|	✓	|	✓	|
[iter()](https://docs.python.org/3/library/functions.html#iter)						|	✓	|	✘	| Potential mutation of objects that are only supposed to be interfaced with through particular methods.
[len()](https://docs.python.org/3/library/functions.html#len)						|	✓	|	✓	|
[license](https://docs.python.org/3/library/constants.html#license)					|	✓	|	✘	| Unnecessary.
[list()](https://docs.python.org/3/library/functions.html#func-list)				|	✓	|	✓	|
[locals()](https://docs.python.org/3/library/functions.html#locals)					|	✓	|	✘	| See globals()
[map()](https://docs.python.org/3/library/functions.html#map)						|	✓	|	✓	|
[max()](https://docs.python.org/3/library/functions.html#max)						|	✓	|	✓	|
[memoryview()](https://docs.python.org/3/library/functions.html#func-memoryview)	|	✓	|	✘	| Potentially non-deterministic outcomes. Consensus failure risk.
[min()](https://docs.python.org/3/library/functions.html#min)						|	✓	|	✓
[next()](https://docs.python.org/3/library/functions.html#next)						|	✓	|	✘	| See iter()
[object()](https://docs.python.org/3/library/functions.html#object)					|	✓	|	✘	| See callable()
[oct()](https://docs.python.org/3/library/functions.html#oct)						|	✓	|	✓	|
[open()](https://docs.python.org/3/library/functions.html#open)						|	✓	|	✘	| File I/O not supported.
[ord()](https://docs.python.org/3/library/functions.html#ord)						|	✓	|	✓	|
[pow()](https://docs.python.org/3/library/functions.html#pow)						|	✓	|	✓	|
[print()](https://docs.python.org/3/library/functions.html#print)					|	✓	|	✓	|
[property()](https://docs.python.org/3/library/functions.html#property)				|	✓	|	✘	| Property creation not supported because classes are disabled.
[range()](https://docs.python.org/3/library/functions.html#func-range)				|	✓	|	✓	|
[repr()](https://docs.python.org/3/library/functions.html#repr)						|	✓	|	✘	| Unnecessary and non-deterministic due to memory address as output of this function. This is a consensus failure risk.
[reversed()](https://docs.python.org/3/library/functions.html#reversed)				|	✓	|	✓
[round()](https://docs.python.org/3/library/functions.html#round)					|	✓	|	✓
[set()](https://docs.python.org/3/library/functions.html#func-set)					|	✓	|	✓
[setattr()](https://docs.python.org/3/library/functions.html#setattr)				|	✓	|	✘	| Arbitrary setting and overwriting of Python attributes has storage corruption and private method access implications.
[slice()](https://docs.python.org/3/library/functions.html#slice)					|	✓	|	✘	| Unnecessary.
[sorted()](https://docs.python.org/3/library/functions.html#sorted)					|	✓	|	✓
[staticmethod()](https://docs.python.org/3/library/functions.html#staticmethod)		|	✓	|	✘	| Static methods are not supported because classes are disabled.
[str()](https://docs.python.org/3/library/functions.html#func-str)					|	✓	|	✓
[sum()](https://docs.python.org/3/library/functions.html#sum)						|	✓	|	✓
[super()](https://docs.python.org/3/library/functions.html#super)					|	✓	|	✘	| Super is not supported because classes are disabled
[tuple()](https://docs.python.org/3/library/functions.html#func-tuple)				|	✓	|	✓
[type()](https://docs.python.org/3/library/functions.html#type)						|	✓	|	✓
[vars()](https://docs.python.org/3/library/functions.html#vars)						|	✓	|	✘	| Allows exploration path into security exploit development.
[zip()](https://docs.python.org/3/library/functions.html#zip)						|	✓	|	✓

## Illegal AST Nodes

Similarly, some of the AST (abstract syntax tree) nodes that make up deeper levels of the Python syntax are not allowed. Mainly, the nodes around the async/await features are restricted.

AST Node 				| Reason for Restriction
-						| -
[ast.AsyncFor](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#AsyncFor)			| All async code is invalid in Contracting.
[ast.AsyncFunctionDef](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#AsyncFunctionDef)	| All async code is invalid in Contracting.
[ast.AsyncWith](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#AsyncWith)			| All async code is invalid in Contracting.
ast.AugLoad				| AST Node never used in current CPython implementation.
ast.AugStore			| AST Node never used in current CPython implementation.
[ast.Await](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Await)				| All async code is invalid in Contracting.
[ast.ClassDef](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#ClassDef)			| Classes are disabled in Contracting.
[ast.Ellipsis](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Ellipsis)			| Ellipsis should not be defined in a smart contract. They may be an effect of one.
[ast.GeneratorExp](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#GeneratorExp)		| Generators hold state that is incompatible with Contracting's model.
[ast.Global](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Global)				| Scope modification could have security implications.
ast.Interactive			| Only available in Python interpreters. Potential security risk.
[ast.MatMult](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#MatMult)				| New AST feature. Not yet widely adopted. Potential security risk.
[ast.Nonlocal](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Nonlocal)			| Scope modification could have security implications.
ast.Suite				| Similar to ast.Interactive
[ast.Yield](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Yield)				| Generator related code is not compatible with Contracting.
[ast.YieldFrom](https://greentreesnakes.readthedocs.io/en/latest/nodes.html#YieldFrom)			| Generator related code is not compatible with Contracting.

### Violations

The linter will check for several violations that will fail your smart contract automatically. Here is a list of the current violations and examples of code that will cause them.

#### S1- Illegal contracting syntax type used
Thrown when an AST type that is not allowed is visited by the linter.

```python
def bad():
	2 @ 2 # ast.MatMul code
```

#### S2- Illicit use of '\_' before variable
\_ is used for gating certain functionality. Using it as a prefix to any variable will cause failure

```python
def bad_var():
	_balances = Hash()
```

#### S3- Illicit use of Nested imports
`import` keywords found inside of functions, loops, etc. will fail.

```python
def bad_import():
	import this_wont_fail

	@construct
	def seed():
		import this_will
```
#### S4- ImportFrom compilation nodes not yet supported
Selective importing is not supported and will fail contracts.
```python
def bad_import():
	from token import send
```
#### S5- Contract not found in lib
Not currently used.
#### S6- Illicit use of classes
Classes are not supported in Contracting and their keywords will fail your contract.

```python
def bad_classes():
	class Car:
		def __init__(self, make, model):
			self.make = make
			self.model = model
```
#### S7- Illicit use of Async functions
Any async related code will fail the contract.
```python
def bad_async():
	async def fail_me():
		pass
```
#### S8- Invalid decorator used
`@export` and `@construct` are the only two decorators allowed in Contracting.
```python
def bad_decorator():
	v = Variable()
	@construct
	def seed():
		v.set(100)

	@export
	def get_v():
		return v.get()

	@unknown
	def this_will_fail():
		pass
```
#### S9- Multiple use of constructors detected
Only a single `@construct` can be included in a contract.

```python
def bad_construct():
	v = Variable()
	@construct
	def seed():
		v.set(123)

	@construct
	def seed_2():
		v.set(999)
```
#### S10- Illicit use of multiple decorators
Stacking decorators is not allowed.

```python
def bad_construct():
	v = Variable()
	@export
	@construct
	def seed():
		v.set(777)
```
#### S11- Illicit keyword overloading for ORM assignments
ORM arguments are injected into the \_\_init\_\_ function on runtime. Messing with these will fail your contract.

```python
def bad_var():
	v = Variable(contract='token')
	w = Variable(driver=None)
	x = Variable(another_kwarg='this will fail')

	@export
	def set():
		v.set(777)
		w.set(999)
		x.set(123)
```
#### S12- Multiple targets to ORM definition detected
Python allows multiple assignment. Trying to do a multiple assignment from an ORM object will fail your contract.
```python
def bad_targets():
	x, y = Hash()
	@export
	def set():
		x['stu'] = 100
		y['stu'] = 999
```
#### S13- No valid contracting decorator found
A contract without a single `@export` decorator is invalid.
```python
def bad_export():
	@construct
	def seed():
		pass
```
#### S14- Illegal use of a builtin
Referencing a builtin that is illegal will fail the contract.
```python
def bad_builtin():
	@export
	def credits():
		return credits
```
#### S15- Reuse of ORM name definition in a function definition argument name
Reuse of any ORM names in any loops, functions, etc. will fail the contract.
```python
def bad_var():
	used_once = Variable()

	@export
	def override():
		used_once = 123
```