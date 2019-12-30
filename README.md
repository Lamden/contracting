# Contracting - Smart Contracts with Python

With Contracting you can write smart contracts in a subset of Python. You can then deploy these contracts to the Lamden Blockchain Cilantro.

Contracting is simply a Python package. Because of this you can use existing Python tooling and the Contracting API to develop smart contracts with ease. That is unlike Solidity, which requires external services like Truffle or TestRPC.

Below is an example of a simple token smart contract in Python. With it you can transfer tokens and check token balances.

```python
def token_contract():
     balances = Hash()
     owner = Variable()
     
     @construct
     def seed():
         owner.set(ctx.caller)

     @export
     def balance_of(wallet_id):
         return balances[wallet_id]

     @export
     def transfer(to, amount):
         balances[ctx.caller] -= amount
         balances[to] += amount
         sender_balance = balances[ctx.caller]

         assert sender_balance >= 0, "Sender balance must be non-negative!!!"

     @export
     def mint(to, amount):
         assert ctx.caller == owner.get(), 'Only the original contract author can mint!'
         balances[to] += amount

```

### Installing

#### Ubuntu 18.04 LTS

Requirements
```
sudo apt-get update
sudo apt-get upgrade
apt install python3-pip
```

Install RocksDB & Dependencies
```
sudo apt-get install libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev librocksdb-dev
```

Install Contracting
```
pip3 install contracting
```

Start Rocks Server
```
rocks serve &
```

#### OSX

Install RocksDB

```
brew install rocksdb
```

If Homebrew is not installed, install it first: https://brew.sh/

Install Contracting
```
pip3 install contracting
```

Start Rocks Server
```
rocks serve &
```

### Using Contracting in a Development Environment

With Contracting now installed, you can develop smart contracts without an instance of the blockchain. This is to improve the speed of development. Here is how you would go about testing a token contract in a Jupyter notebook / IPython console:

```python
In [1]: from contracting.client import ContractingClient

In [2]: def token_contract():
   ...:
   ...:     balances = Hash()
   ...:     owner = Variable()
   ...:     
   ...:     @construct
   ...:     def seed():
   ...:         owner.set(ctx.caller)
   ...:
   ...:     @export
   ...:     def balance_of(wallet_id):
   ...:         return balances[wallet_id]
   ...:
   ...:     @export
   ...:     def transfer(to, amount):
   ...:         balances[ctx.caller] -= amount
   ...:         balances[to] += amount
   ...:         sender_balance = balances[ctx.caller]
   ...:
   ...:         assert sender_balance >= 0, "Sender balance must be non-negative!!!"
   ...:
   ...:     @export
   ...:     def mint(to, amount):
   ...:         assert ctx.caller == owner.get(), 'Only the original contract author can mint!'
   ...:         balances[to] += amount
   ...:

In [3]: client = ContractingClient(signer='stu')

In [4]: client.submit(token_contract, name='token')

In [5]: token = client.get_contract('token')

In [6]: token.mint(to='stu', amount=100000)

In [7]: token.balance_of(wallet_id='stu')
Out[7]: 100000
```

### Get started with Contracting by Example

1. [A very simple Counter contract](/examples/01%20A%20very%20simple%20Counter%20contract.ipynb)
2. [Ingredients of a Smart Contract](/examples/02%20Ingredients%20of%20a%20Smart%20Contract.ipynb)
3. [Interacting with the Client](/examples/03%20Interacting%20with%20the%20Client.ipynb)
4. [Standard Library and Extending Contracting](/examples/04%20Standard%20Library%20and%20Extending%20Contracting.ipynb)
5. [Imports and Advanced Data Storage](/examples/05%20Imports%20and%20Advanced%20Data%20Storage.ipynb)

## FAQs

### `pip install contracting` is not installing on my computer!

If you're using a Mac, you can run into the problem that the C libraries required for Contracting are not getting compiled and the package fails to install.

To fix this:

1. Upgrade XCode
2. Upgrade all software and restart your computer
3. Run `xcode-select --install`.
4. Run `pip install contracting` again.
5. Run `open /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg` if this does not work.
6. Install the package and run `pip install contracting` again. It should work now.
