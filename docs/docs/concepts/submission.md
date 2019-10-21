## How It Works

When a smart contrat is submitted, it goes through a special `submission` smart contract that is seeded at the beginning of the software's lifecycle.

The submission contract is something that bypasses the traditional linting and compilation processes and thus provides a gateway between deeper levels of the Contracting protocol and the 'whitelisted' interfaces of the execution environment.

#### submission.s.py
```python
@__export('submission')
def submit_contract(name, code, owner=None, constructor_args={}):
    __Contract().submit(name=name, code=code, owner=owner, constructor_args=constructor_args)
```

The main concept is that generally \_\_ variables are private and not allowed. However, this code is injected into the state space before the software starts up. Once it is in the state, the `__Contract` object can never be submitted in another smart contract by the user because it will fail.

Calling on the `submit_contract` function will then call `__Contract` which is a special ORM object. `__Contract`'s only job is to submit contracts.

```python
class Contract:
    def __init__(self, driver: ContractDriver=driver):
        self._driver = driver

    def submit(self, name, code, owner=None, constructor_args={}):

        c = ContractingCompiler(module_name=name)

        code_obj = c.parse_to_code(code, lint=True)

        scope = env.gather()
        scope.update({'__contract__': True})
        scope.update(rt.env)

        exec(code_obj, scope)

        if scope.get(config.INIT_FUNC_NAME) is not None:
            scope[config.INIT_FUNC_NAME](**constructor_args)

        self._driver.set_contract(name=name, code=code_obj, owner=owner, overwrite=False)
```

The code that is submitted is put through the `ContractingCompiler` with the `lint` flag set as true. This causes the code to be run through all of the checks and transformed into pure Contracting code, which has slight variations to the code that the user submits but is used internally by the system.

`__Contract` will then gather the working environment and execute it on the submitted code. This encapsulates the execution environment completely within the new code module without potential leakage or exposure. The `__contract__` flag is also set to indicate to the Python import system that this code cannot use any builtins at runtime.

`__Contract` will then try to see if there is a `@construct` function available on the code. If this is the case, it will execute this function and pass the constructor arguments into it if any are provided.

Finally, the code string, as compiled, is stored in the state space so that other contracts can import it and users can transact upon it.

## Linter

The Contracting Linter is a `NodeVisitor` from the Python AST module. It takes a string of code and turns it into an abstract syntax tree which it then traverses. Upon visiting of each type of node, the linter will do certain checks to make sure that the code is inline with what is allowed in the Contracting execution environment. You can see some of the things it checks for in the 'Valid Code' section under 'Violations'.

If there are no violations, the code is then passed to the compiler which does the final checks.

## Compiler

The Contracting Compiler takes the linted code and uses a `NodeTransformer` object from the Python AST module to turn the code into a lower representation of what it should be so that Contracting can directly execute functions against it.

Some of these transforms include appending `__` to `@export` decorators and variables, renaming the `@construct` function to `____`, and inserting the correct keyword arguments into the ORM initialization functions.

Here is an example of what code looks like before and after it goes through the compiler.

#### Before
```python
balances = Hash()

@construct
def seed():
    balances['stu'] = 1000000

@export
def transfer(amount, to):
    sender = ctx.signer
    assert balances[sender] >= amount

    balances[sender] -= amount

    if balances[to] is None:
        balances[to] = amount
    else:
        balances[to] += amount

@export
def balance(account):
    return balances[account]
```
#### After
```python
__balances = Hash(contract='__main__', name='balances')


def ____():
    __balances['stu'] = 1000000


@__export('__main__')
def transfer(amount, to):
    sender = ctx.signer
    assert __balances[sender] >= amount
    __balances[sender] -= amount
    if __balances[to] is None:
        __balances[to] = amount
    else:
        __balances[to] += amount


@__export('__main__')
def balance(account):
    return __balances[account]
```