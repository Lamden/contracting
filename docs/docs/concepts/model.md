## Python
Contracting is 100% compatible Python code with a few modifications to make it more deterministic on different machines and safer in untrusted environments. You need to have knowledge of Python to be able to use Contracting.

If you do not know Python, try one of these resources:

1. Official documentation
2. Learn Python in Y Minutes
3. Sendtex YouTube videos

## What is a smart contract, anyways?

Let's define what a smart contract is, and what one isn't.

A smart contract is: 						| A smart contract isn't:
-					 						| -
Immutable			 						| A full application
Open-Sourced								| A database
Accessible through strict API 				| Able to act without interaction
A set of rules enforced by consensus 		| Able to draw data from the web arbitrarily
A function of it's inputs

Therefore, we have to make some considerations and alterations to what is allowed in a smart contract. We do not add any additional features to Python that make the code incompatible. Contracting is a strict subset.

### How Code Executes Usually
In Python, you write code, run it, and it executes. It is either something that happens in sequence and then finishes, or is a long running asynchronous application such as a web server that runs in an event loop and processes requests over a long period of time.

Smart contracts do neither of these things!

### How Smart Contract Code Executes
Smart contracts define an explicit API that one can call. To execute code, 

