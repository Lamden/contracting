# Contracting - Smart Contracts with Python

With Contracting you can write smart contracts in a subset of Python. You can then deploy these contracts to the Lamden Blockchain Cilantro.

Contracting is simply a Python package. Because of this you can use existing Python tooling and the Contracting API to develop smart contracts with ease. That is unlike Solidity, which requires external services like Truffle or TestRPC.

Below is an example of a simple token smart contract in Python. With it you can transfer tokens and check token balances.

```python
def token_contract():
    from contracting.libs.datatypes import hmap

    balances = hmap('balances', str, int)

    @export
    def balance_of(wallet_id):
        return balances[wallet_id]

    @export
    def transfer(to, amount):
        balances[rt['sender']] -= amount
        balances[to] += amount
        sender_balance = balances[rt['sender']]

        assert sender_balance >= 0, "Sender balance must be non-negative!!!"

    @export
    def mint(to, amount):
        assert rt['sender'] == rt['author'], 'Only the original contract author can mint!'
        balances[to] += amount
```

### Installing

```
git clone https://github.com/Lamden/contracting.git
cd contracting
git pull origin dev
python3 setup.py develop

brew install redis
brew services start redis
```

### Using Contracting in a Development Environment

With Contracting now installed, you can develop smart contracts without an instance of the blockchain. This is to improve the speed of development. Here is how you would go about testing a token contract in a Jupyter notebook / IPython console:

```python
In [1]: from contracting.tooling import *

In [2]: def token_contract():
   ...:     from contracting.libs.datatypes import hmap
   ...:
   ...:     balances = hmap('balances', str, int)
   ...:
   ...:     @export
   ...:     def balance_of(wallet_id):
   ...:         return balances[wallet_id]
   ...:
   ...:     @export
   ...:     def transfer(to, amount):
   ...:         balances[rt['sender']] -= amount
   ...:         balances[to] += amount
   ...:         sender_balance = balances[rt['sender']]
   ...:
   ...:         assert sender_balance >= 0, "Sender balance must be non-negative!!!"
   ...:
   ...:     @export
   ...:     def mint(to, amount):
   ...:         assert rt['sender'] == rt['author'], 'Only the original contract author can mint!'
   ...:         balances[to] += amount
   ...:

In [3]: d = default_driver()
   ...: d.r.flushdb()
Out[3]: True

In [4]: d.publish_function(token_contract, contract_name='token', author='stu')

In [5]: token = ContractWrapper('token', default_sender='stu')

In [6]: token.mint(to='stu', amount=100000)
Out[6]: {'status': 'success', 'output': None, 'remaining_stamps': 0}

In [7]: token.balance_of(wallet_id='stu')
Out[7]: {'status': 'success', 'output': Decimal('100000'), 'remaining_stamps': 0}
```

### Get started with Contracting by Example

1. [A very simple Counter contract](/examples/01%20A%20very%20simple%20Counter%20contract.ipynb)
2. [Ingredients of a Smart Contract](/examples/02%20Ingredients%20of%20a%20Smart%20Contract.ipynb)
3. [Interacting with the Client](/examples/03%20Interacting%20with%20the%20Client.ipynb)
4. [Standard Library and Extending Contracting](/examples/04%20Standard%20Library%20and%20Extending%20Contracting.ipynb)
5. [Imports and Advanced Data Storage](/examples/05%20Imports%20and%20Advanced%20Data%20Storage.ipynb)

### Storage Model

Contracting uses Redis to store the state of the blockchain. This means you can use any Redis tooling to inspect the storage and retrieval of information to and from your smart contracts.

You can also use a GUI like Medis without any issue.

![Medis](medis.png)

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
