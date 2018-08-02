# Seneca Smart Contracts

<img src="https://github.com/Lamden/seneca/raw/master/seneca.jpg" align="right"
     title="Seneca" width="150" height="275">

Seneca is a Turing-incomplete domain specific language (DSL) for writing smart contracts on the Lamden Cilantro blockchain. The philosophy is that smart contracts in practice are mainly used for data storage, access, and modification, so the blockchain data and processing should be looked at more as a public database rather than a world computer.

This philosophy improves security as the limitations of the contracts are locked in at pure storage, access, and modification of data tables rather than Turing-complete computing which has infinite numbers of attack vectors.

### What's a smart contract?
* Smart contracts are code that run on the blockchain. They let users model many aspects of traditional agreements and transfer assets which are stored in the blockchain, the most obvious example being crypto currency.

## How is Seneca different?
The primary design goal of Seneca is to be easy to use and easy to reason about. Seneca is a variant of the programming language Python. We chose Python because it has a very large active community, has extensive existing documentation and tutorials, and is known for being beginner-friendly.

### Reusable components ###
Seneca has a simple model for sharing code and building libraries based on Python module imports. The only difference from standard Python being exports are explicit (in a style similar to Node.js) so contract authors have control over what methods are available to other modules.

### Execution model ###
Seneca contracts run in two modes. In the first, the contract is run directly as the primary module. Just like Python, when the module is run directly, the variable \_\_name\_\_ has its value set to the string '\_\_main\_\_'. When a contract is uploaded to the network, it's run directly (as the primary module) exactly once. During this execution the contract can set up database tables, populate them with data, import other existing contracts, and call methods on those contracts.

After the contract has been run directly and written to the blockchain, if it has exported functions, other contracts can import it and call those functions.

### Security ###
Permissions and security are also easy to implement and reason about. Each contract can create and store data on the block chain. This data is only writable from the contract that created it and all table are isolated in a dedicated per contact namespace. The inspiration for this is same origin policy used on the web, with each contract analogous to an entire domain.

The only way for other contracts to edit data owned by a contract is to import it and call its functions (if the author has created those functions).

Any restrictions over how and when those functions are run is coded in an imperative style in the functions themselves.
