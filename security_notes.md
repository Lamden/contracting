# Security

## Model

* Contracts can be run in two different modes:
  * As the primary contract
    * This occurs only once when the contract is successfully added to the block chain
    * When this occurs per the python convention the builtin variable __name__ has the value '__main__'
  * Imported by another contract
    * Once the contract has run as a primary contract and is part of the blockchain, it can be imported by other contracts.
    * This could happen an unlimited number of times
    * Unlike typical Python where all functions and module-global variables are automatically exported, in Seneca, exports must be done explicitly.
    * If nothing is exported, a new contract attempting to import it will crash.

* Each contract can create its own isolated data store accessible via a tabular SQL-like API and a soon to be added key value store API
* The only way to directly edit a contract's data is via functions in, and (potentially) exported by that contract.
* If a contract author wants to allow others to modify the contract's data, functions that specifically do that must be exported
* The only modules contracts are allowed to import are Seneca library modules and other contracts
* Contracts have access to __name__ and seneca.runtime data to know who called the contract, what run mode it's in, who submitted the module to the blockchain, if it's imported by another contract, which user submitted the other contract to the blockchain, etc.
  * This data can be used to control access to the contract in general, or specific features.

## Execution

* Before execution begins, the modules AST is scanned to make sure all AST nodes are in the whitelist
* Modules only have access to limited functionality in the Seneca lib and other importable smart contracts on the blockchain
* Smart contracts will each run in their own dedicated Seneca interpreter running inside an OS container
* When contracts are imported, they will actually be run in a separate dedicated Seneca interpreter (and container), exported names will be used to generate a skeleton module imported by the primary contract with the same names available as the real imported contract, but with functionality replaced with RPCs that bridge the containers and trigger execution of the imported module. Any data returned by those functions will be serialized and sent back across the container boundary.

* Data access will work very similarly to imported contracts. The data store will run in an isolated container, and calls will be serialized and sent between the containers
  * Validation/authorization will be done in the data store container
