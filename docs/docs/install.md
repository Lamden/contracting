# Installation

1. Python 3.6.8
    * https://www.python.org/downloads/release/python-368/
2. MongoDB Community Edition
    * https://docs.mongodb.com/manual/administration/install-community/
    * Be sure to start MongoDB before continuing.
3. Contracting
    * In a command terminal, run `pip3 install contracting`

## Testing the Installation
Open the Python 3.6.8 REPL, usually by running `python3` in a command terminal. Type the following commands.
```python
In [1]: from contracting.client import ContractingClient
In [2]: client = ContractingClient()
In [3]: client.get_contracts()
Out[3]: ['submission'] 
```
If your output matches, you've successfully installed Contracting. Welcome to the most advance smart contacting system on the planet!