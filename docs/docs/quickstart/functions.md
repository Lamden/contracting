## Executing Functions

A smart contract is not interesting without interaction. This is where the `@export` decorator comes into play. As a smart contract developer, you choose which functions you want to allow other people to call. All functions are private by default. Only functions that have an `@export` decorator above them are callable by an outside party.

To call a function on a smart contract, we have to pull the contract back out from the state space.
```python
hello_world = client.get_contract('hello_world')
hello_world
```
```python
>> <contracting.client.AbstractContract at 0x1130748d0>
```

You can pull contracts out from the state space and into an Abstract Contract object that then allows deeper interaction. The client takes care of creating all of the attributes for you. All exported functions are automatically available on the contract once you pull them.

```python
hello_world.hello()
```
```
>> 'World!'
```

It works!

## Private Functions

We added a private function to the Hello, World! contract as well. Private functions do not have `@export` above them. A user cannot call a private function. However, the smart contract itself can call a private function within itself.

This is how the `add` function actually adds. While contrived, this example illustrates how private functions behave.

## Keyword Arguments

Functions that take arguments expect keyword arguments passed in. Positional arguments are not supported and will cause an error.

Here is how we call our `add` function.

```python
hello_world.add(a=2, b=3)
```
```
5
```

Here is what happens if we do not use keyword arguments.

```python
hello_world.add(2, 3)
```
```python
TypeError: _abstract_function_call() got multiple values for argument 'signer'
```

### Try it for yourself

1. Write your own smart contract that has 3 different exported functions.
2. Write a function that is not exported that one of your exported functions calls. 
3. Submit the smart contract into the state space.
4. Pull it back out as an Abstract Contract.
5. Call each function and verify that it works as expected.
