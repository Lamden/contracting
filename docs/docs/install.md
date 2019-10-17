# Installation

## RocksDB for Storage
Contracting uses RocksDB for storage. RocksDB is a high performance key value storage system. You need to install RocksDB first by using their guide found here.

Note: for Linux, you will have to `make` the software. For Windows, you will have to compile it with Visual Studio. Only Mac supports RocksDB from a package manager.

Once RocksDB is successfully installed, install Lamden's RocksDB wrapper by typing in `pip3 install rocks` and wait for the installation to finish.

Now, start a `rocks` server instance by running `rocks serve` in your command line terminal. You should see the following ASCII art pop up. This means that you were successful.

<center><img src='/img/rocks-serve.png' alt='Rocks Serve' width=50%></center>

You can test to make sure you can modify the state of the database by running some CLI commands like so:

<center><img src='/img/rocks-cli.png' alt='Rocks CLI' width=100%></center>


## Contracting
Now, install Contracting via pip: `pip3 install contracting`. With `rocks` running, you will be able to import the Contracting client. To test if you were successful, open up a Python REPL `python3` or `ipython` and type:

```python
In [1]: from contracting.client import ContractingClient
In [2]: client = ContractingClient()
In [3]: client.get_contracts()
Out[3]: ['submission'] 
```
If your output matches, you've successfully installed Contracting. Welcome to the most advance smart contacting system on the planet!