# Seneca Smart Contracts

Seneca is a turing-incomplete domain specific language (DSL) for writing smart contracts on the Lamden Cilantro blockchain. The philosophy is that smart contracts in practice are mainly used for data storage, access, and modification, so the blockchain data and processing should be looked at more as a public database rather than a world computer.

This philosophy improves security as the limitations of the contracts are locked in at pure storage, access, and modification of data tables rather than turing-complete computing which has infinate numbers of attack vectors.

### What's a smart contract?

A Seneca smart contract is a short script that describes a constructor, local storage table, access control, setters, and getters. This script is parsed by the participants of the blockchain into a pure CQL query stack which is then hashed and agreed upon by the delegates of the system.

For example:

Some script -> DSL parser -> ['SELECT * FROM users', 'INSERT...'] 

### Types

Types are derived from Cassandra types specifically so that it is easy to remember how smart contracts should be written.

int

bigint

text

#### Insert Queries
```
insert { 
	key : value, 
    key : value
}
into table_name
if not exists
```

#### Delete Queries
```
delete user
from table_name
if user.balance == 0
```
